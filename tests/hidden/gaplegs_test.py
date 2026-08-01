"""tests/hidden/gaplegs_test.py — 缺口路段补测（scripts/gap_legs.py）的全面契约测试。

覆盖 build_graph / shortest_path（纯函数，固定 Overpass JSON 夹具）、
fetch_elevations（monkeypatch 掉 subprocess.run，覆盖分段 / null 插值 / 重试）、
build_leg（两条分支：OSM 步道连通 与 不连通回退大圆折线；往返 out_and_back）、
main（离线幂等：文件齐备时不打网络，缺失/不全/--refresh 时才调用 build_leg）。

一次网络请求都不发。
"""
import json
import math
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gap_legs  # noqa: E402


LEG_IDS = [
    "namche-everest-view",
    "dingboche-nangkartshang",
    "lobuche-pheriche",
    "pheriche-pangboche",
]


def _haversine_m(lat1, lon1, lat2, lon2):
    """标准 haversine，地球半径 6371000 m（期望值计算用，不依赖 geo.py stub）。"""
    radius = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _overpass_json(ways):
    """把 [(way_id, [(node_id, lat, lon), ...]), ...] 组装成 Overpass `out body geom` 形态。"""
    elements = []
    for way_id, node_specs in ways:
        elements.append(
            {
                "type": "way",
                "id": way_id,
                "nodes": [n for n, _, _ in node_specs],
                "geometry": [{"lat": lat, "lon": lon} for _, lat, lon in node_specs],
            }
        )
    return {"elements": elements}


def _elevation_response(elevations, status="OK"):
    """构造 opentopodata /v1/srtm30m 的响应体（JSON 字符串）。"""
    return json.dumps(
        {
            "results": [{"elevation": e, "location": {"lat": 0.0, "lng": 0.0}} for e in elevations],
            "status": status,
        }
    )


def _run_sequence(monkeypatch, responses):
    """monkeypatch 掉 gap_legs 里对 subprocess.run 的调用，按顺序依次返回 responses 里的假响应。

    直接替换模块命名空间里的 "subprocess" 名字（raising=False）而不是
    `gap_legs.subprocess.run`：这样无论 gap_legs.py 当前是否已经 `import subprocess`，
    都能在不打网络的前提下拦截调用，实现落地后同样生效。
    """
    calls = []
    it = iter(responses)

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return next(it)

    monkeypatch.setattr(gap_legs, "subprocess", types.SimpleNamespace(run=fake_run), raising=False)
    return calls


def _patch_overpass(monkeypatch, overpass_json):
    """monkeypatch 让 gap_legs 里对 subprocess.run 的调用都返回固定的 Overpass JSON。"""
    fake_run = lambda *a, **k: types.SimpleNamespace(  # noqa: E731
        returncode=0, stdout=json.dumps(overpass_json), stderr=""
    )
    monkeypatch.setattr(gap_legs, "subprocess", types.SimpleNamespace(run=fake_run), raising=False)


def _counting_build_leg():
    """记录 leg_id 调用顺序的假 build_leg，返回一个形态合法的 leg 字典。"""
    calls = []

    def fake(leg_id, start, goal, bbox, out_and_back=False, **kwargs):
        calls.append(leg_id)
        return {"id": leg_id, "points": [[86.0, 27.0, 3000.0]], "source": "OSM+SRTM30m"}

    return fake, calls


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------


def test_gaplegs_build_graph_shared_node_connects_two_ways():
    """共享 node id 的两条 way 应视为一张连通图（用 shortest_path 验证可达）。"""
    overpass_json = _overpass_json(
        [
            (1, [(10, 27.80, 86.70), (11, 27.81, 86.71)]),
            (2, [(11, 27.81, 86.71), (12, 27.82, 86.72)]),
        ]
    )

    nodes, adj = gap_legs.build_graph(overpass_json)

    assert gap_legs.shortest_path(nodes, adj, 10, 12) is not None


def test_gaplegs_build_graph_edge_weight_equals_haversine_distance():
    """边权必须等于相邻 geometry 点的 haversine 米数，而不是任意占位值。"""
    a, b = (27.9478, 86.8104), (27.9470, 86.8100)
    overpass_json = _overpass_json([(1, [(1, *a), (2, *b)])])

    nodes, adj = gap_legs.build_graph(overpass_json)

    neighbors_of_1 = dict(adj[1])
    assert neighbors_of_1[2] == pytest.approx(_haversine_m(*a, *b), rel=1e-6)


def test_gaplegs_build_graph_empty_elements_returns_empty_graph():
    """没有 way 元素时返回两个空字典，不报错。"""
    nodes, adj = gap_legs.build_graph({"elements": []})

    assert nodes == {}
    assert adj == {}


def test_gaplegs_build_graph_single_way_produces_linear_degree_sequence():
    """单条 4 节点 way：两端度数为 1，中间两点度数为 2（无环、无额外连边）。"""
    overpass_json = _overpass_json(
        [(1, [(10, 27.0, 86.0), (11, 27.001, 86.001), (12, 27.002, 86.002), (13, 27.003, 86.003)])]
    )

    nodes, adj = gap_legs.build_graph(overpass_json)

    assert len(adj[10]) == 1
    assert len(adj[13]) == 1
    assert len(adj[11]) == 2
    assert len(adj[12]) == 2


# ---------------------------------------------------------------------------
# shortest_path
# ---------------------------------------------------------------------------


def test_gaplegs_shortest_path_start_equals_goal_returns_single_point():
    """start 与 goal 相同的节点时，返回只含该点的单元素列表。"""
    nodes = {1: (27.80, 86.70)}
    adj = {1: []}

    path = gap_legs.shortest_path(nodes, adj, 1, 1)

    assert path == [(27.80, 86.70)]


def test_gaplegs_shortest_path_returns_none_when_disconnected():
    """两个互不相连的分量之间应返回 None。"""
    nodes = {1: (27.80, 86.70), 2: (27.90, 86.80)}
    adj = {1: [], 2: []}

    assert gap_legs.shortest_path(nodes, adj, 1, 2) is None


def test_gaplegs_shortest_path_prefers_lower_total_weight_over_fewer_hops():
    """Dijkstra 应选总权重更低的多跳路径，而不是权重更高的直连单跳边。"""
    nodes = {1: (0.0, 0.0), 2: (0.0, 0.001), 3: (0.0, 0.002)}
    adj = {
        1: [(3, 1000.0), (2, 10.0)],
        2: [(1, 10.0), (3, 10.0)],
        3: [(1, 1000.0), (2, 10.0)],
    }

    path = gap_legs.shortest_path(nodes, adj, 1, 3)

    assert path == [(0.0, 0.0), (0.0, 0.001), (0.0, 0.002)]


@pytest.mark.parametrize(
    "start_id, goal_id",
    [(999, 2), (1, 999)],
    ids=["missing-start", "missing-goal"],
)
def test_gaplegs_shortest_path_missing_id_raises_keyerror(start_id, goal_id):
    """start_id 或 goal_id 不在图里时抛 KeyError。"""
    nodes = {1: (0.0, 0.0), 2: (0.0, 0.001)}
    adj = {1: [(2, 10.0)], 2: [(1, 10.0)]}

    with pytest.raises(KeyError):
        gap_legs.shortest_path(nodes, adj, start_id, goal_id)


# ---------------------------------------------------------------------------
# fetch_elevations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "n_points, expected_calls",
    [(5, 1), (100, 1), (101, 2), (150, 2), (200, 2)],
    ids=["small-single-call", "exactly-100-one-call", "101-two-calls", "150-two-calls", "200-two-calls"],
)
def test_gaplegs_fetch_elevations_batches_at_most_100_per_request(monkeypatch, n_points, expected_calls):
    """每请求 ≤100 个 locations：超过 100 个点必须拆成多次请求，结果与输入等长。"""
    pts = [(27.0 + 0.0001 * i, 86.0 + 0.0001 * i) for i in range(n_points)]
    responses = []
    remaining = n_points
    while remaining > 0:
        batch_n = min(100, remaining)
        responses.append(
            types.SimpleNamespace(returncode=0, stdout=_elevation_response([3000.0] * batch_n), stderr="")
        )
        remaining -= batch_n
    calls = _run_sequence(monkeypatch, responses)

    result = gap_legs.fetch_elevations(pts)

    assert len(calls) == expected_calls
    assert len(result) == n_points
    assert result == pytest.approx([3000.0] * n_points)


def test_gaplegs_fetch_elevations_concatenates_batches_in_order(monkeypatch):
    """多批结果必须按原始点序拼接，不能错位或倒序（用可区分的数值序列验证）。"""
    pts = [(27.0 + 0.0001 * i, 86.0 + 0.0001 * i) for i in range(150)]
    batch1 = [float(i) for i in range(100)]
    batch2 = [float(100 + i) for i in range(50)]
    _run_sequence(
        monkeypatch,
        [
            types.SimpleNamespace(returncode=0, stdout=_elevation_response(batch1), stderr=""),
            types.SimpleNamespace(returncode=0, stdout=_elevation_response(batch2), stderr=""),
        ],
    )

    result = gap_legs.fetch_elevations(pts)

    assert result[0] == pytest.approx(0.0)
    assert result[99] == pytest.approx(99.0)
    assert result[100] == pytest.approx(100.0)
    assert result[149] == pytest.approx(149.0)


def test_gaplegs_fetch_elevations_interpolates_null_values_linearly(monkeypatch):
    """返回 null 的点用相邻有效值线性补，而不是留 None 或补 0。"""
    pts = [(27.0, 86.0), (27.001, 86.001), (27.002, 86.002), (27.003, 86.003)]
    eles = [100.0, None, None, 130.0]
    _run_sequence(monkeypatch, [types.SimpleNamespace(returncode=0, stdout=_elevation_response(eles), stderr="")])

    result = gap_legs.fetch_elevations(pts)

    assert result[0] == pytest.approx(100.0)
    assert result[1] == pytest.approx(110.0, abs=0.5)
    assert result[2] == pytest.approx(120.0, abs=0.5)
    assert result[3] == pytest.approx(130.0)


def test_gaplegs_fetch_elevations_retries_then_succeeds(monkeypatch):
    """前两次失败（非 OK status），第三次成功：应返回正确结果，不提前抛错。"""
    pts = [(27.0, 86.0)]
    fail_resp = types.SimpleNamespace(returncode=0, stdout=_elevation_response([], status="UNKNOWN_ERROR"), stderr="")
    ok_resp = types.SimpleNamespace(returncode=0, stdout=_elevation_response([3000.0]), stderr="")
    calls = _run_sequence(monkeypatch, [fail_resp, fail_resp, ok_resp])

    result = gap_legs.fetch_elevations(pts)

    assert result == pytest.approx([3000.0])
    assert len(calls) == 3


def test_gaplegs_fetch_elevations_raises_after_retries_exhausted_on_bad_status(monkeypatch):
    """status 持续非 OK：重试 3 次后抛 RuntimeError。"""
    pts = [(27.0, 86.0)]
    bad_resp = types.SimpleNamespace(returncode=0, stdout=_elevation_response([], status="UNKNOWN_ERROR"), stderr="")
    calls = _run_sequence(monkeypatch, [bad_resp, bad_resp, bad_resp])

    # 精确匹配 RuntimeError 本身，不接受 NotImplementedError 等子类蒙混过关。
    with pytest.raises(RuntimeError) as excinfo:
        gap_legs.fetch_elevations(pts)

    assert excinfo.type is RuntimeError
    assert len(calls) == 3


def test_gaplegs_fetch_elevations_raises_after_retries_exhausted_on_http_failure(monkeypatch):
    """curl 持续以非零 returncode 失败（HTTP 失败）：重试 3 次后抛 RuntimeError。"""
    pts = [(27.0, 86.0)]
    fail_resp = types.SimpleNamespace(returncode=22, stdout="", stderr="curl: (22) The requested URL returned error")
    calls = _run_sequence(monkeypatch, [fail_resp, fail_resp, fail_resp])

    # 精确匹配 RuntimeError 本身，不接受 NotImplementedError 等子类蒙混过关。
    with pytest.raises(RuntimeError) as excinfo:
        gap_legs.fetch_elevations(pts)

    assert excinfo.type is RuntimeError
    assert len(calls) == 3


# ---------------------------------------------------------------------------
# build_leg
# ---------------------------------------------------------------------------


def test_gaplegs_build_leg_uses_osm_path_when_connected(monkeypatch):
    """OSM 步道连通时点序列取自该步道，source 里不出现「不连通」。"""
    start = (27.8054, 86.7124)
    goal = (27.8116, 86.7183)
    mid = (27.8085, 86.7150)
    overpass_json = _overpass_json([(1, [(1, *start), (2, *mid), (3, *goal)])])
    _patch_overpass(monkeypatch, overpass_json)
    monkeypatch.setattr(gap_legs, "fetch_elevations", lambda pts: [3000.0 + 10 * i for i in range(len(pts))])

    leg = gap_legs.build_leg(
        "namche-everest-view", start=start, goal=goal, bbox=(86.70, 27.80, 86.72, 27.82), out_and_back=False
    )

    assert leg["id"] == "namche-everest-view"
    assert "不连通" not in leg["source"]
    assert len(leg["points"]) == 3
    assert leg["points"][0][:2] == pytest.approx([start[1], start[0]], abs=1e-4)
    assert leg["points"][-1][:2] == pytest.approx([goal[1], goal[0]], abs=1e-4)


def test_gaplegs_build_leg_passes_path_points_to_fetch_elevations_in_order(monkeypatch):
    """build_leg 必须把路径点按顺序、以 (lat, lon) 形态交给 fetch_elevations 采样。"""
    start = (27.8054, 86.7124)
    goal = (27.8116, 86.7183)
    mid = (27.8085, 86.7150)
    overpass_json = _overpass_json([(1, [(1, *start), (2, *mid), (3, *goal)])])
    _patch_overpass(monkeypatch, overpass_json)

    received = []

    def fake_fetch(pts):
        received.append(list(pts))
        return [3000.0 + 10 * i for i in range(len(pts))]

    monkeypatch.setattr(gap_legs, "fetch_elevations", fake_fetch)

    gap_legs.build_leg(
        "namche-everest-view", start=start, goal=goal, bbox=(86.70, 27.80, 86.72, 27.82), out_and_back=False
    )

    assert len(received) == 1
    assert received[0] == pytest.approx([start, mid, goal])


def test_gaplegs_build_leg_out_and_back_mirrors_forward_path(monkeypatch):
    """out_and_back=True 时点序列是单程加反向，首末点重合于起点。"""
    start = (27.8054, 86.7124)
    goal = (27.8116, 86.7183)
    mid = (27.8085, 86.7150)
    overpass_json = _overpass_json([(1, [(1, *start), (2, *mid), (3, *goal)])])
    _patch_overpass(monkeypatch, overpass_json)
    monkeypatch.setattr(gap_legs, "fetch_elevations", lambda pts: [3000.0 + 10 * i for i in range(len(pts))])

    leg = gap_legs.build_leg(
        "namche-everest-view", start=start, goal=goal, bbox=(86.70, 27.80, 86.72, 27.82), out_and_back=True
    )

    pts = leg["points"]
    assert pts[0][:2] == pytest.approx([start[1], start[0]], abs=1e-4)
    assert pts[-1][:2] == pytest.approx([start[1], start[0]], abs=1e-4)
    # 单程 3 点，往返应为 2*3-1=5（不重复折返点）或 2*3=6（重复折返点）
    assert len(pts) in (5, 6)
    lons_lats = [tuple(p[:2]) for p in pts]
    assert any(
        lon == pytest.approx(goal[1], abs=1e-4) and lat == pytest.approx(goal[0], abs=1e-4)
        for lon, lat in lons_lats
    )


def test_gaplegs_build_leg_falls_back_to_great_circle_when_disconnected(monkeypatch):
    """OSM 步道两端不连通时回退为端点间大圆折线，按 100 m 间隔取点，source 标明「不连通」。"""
    start = (27.9478, 86.8104)  # Lobuche
    goal = (27.8941, 86.8198)  # Pheriche
    overpass_json = _overpass_json(
        [
            (1, [(10, *start), (11, 27.9470, 86.8100)]),
            (2, [(20, *goal), (21, 27.8945, 86.8202)]),
        ]
    )
    _patch_overpass(monkeypatch, overpass_json)
    monkeypatch.setattr(gap_legs, "fetch_elevations", lambda pts: [4900.0] * len(pts))

    leg = gap_legs.build_leg(
        "lobuche-pheriche", start=start, goal=goal, bbox=(86.79, 27.88, 86.82, 27.95), out_and_back=False
    )

    assert "不连通" in leg["source"]
    pts = leg["points"]
    assert len(pts) >= 2

    total_m = _haversine_m(*start, *goal)
    expected_n = round(total_m / 100.0) + 1
    assert len(pts) == pytest.approx(expected_n, abs=3)

    first_dist = _haversine_m(pts[0][1], pts[0][0], start[0], start[1])
    last_dist = _haversine_m(pts[-1][1], pts[-1][0], goal[0], goal[1])
    assert first_dist < 5.0
    assert last_dist < 5.0


def test_gaplegs_build_leg_fallback_out_and_back_endpoints_coincide(monkeypatch):
    """回退分支叠加 out_and_back=True 时，首末点仍应重合。"""
    start = (27.9478, 86.8104)
    goal = (27.8941, 86.8198)
    overpass_json = _overpass_json(
        [
            (1, [(10, *start), (11, 27.9470, 86.8100)]),
            (2, [(20, *goal), (21, 27.8945, 86.8202)]),
        ]
    )
    _patch_overpass(monkeypatch, overpass_json)
    monkeypatch.setattr(gap_legs, "fetch_elevations", lambda pts: [4900.0] * len(pts))

    leg = gap_legs.build_leg(
        "lobuche-pheriche", start=start, goal=goal, bbox=(86.79, 27.88, 86.82, 27.95), out_and_back=True
    )

    pts = leg["points"]
    assert pts[0][:2] == pytest.approx(pts[-1][:2], abs=1e-4)
    assert "不连通" in leg["source"]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_gaplegs_main_skips_build_leg_when_file_already_has_all_four_legs(tmp_path, monkeypatch):
    """OUT 文件已存在且含全部 4 个 leg id 时，main() 不发网络请求（不调用 build_leg）。"""
    out_path = tmp_path / "gap-legs.json"
    existing = {lid: {"id": lid, "points": [[86.0, 27.0, 3000.0]], "source": "s"} for lid in LEG_IDS}
    out_path.write_text(json.dumps(existing), encoding="utf-8")
    monkeypatch.setattr(gap_legs, "OUT", out_path)

    fake_build_leg, calls = _counting_build_leg()
    monkeypatch.setattr(gap_legs, "build_leg", fake_build_leg)

    gap_legs.main()

    assert len(calls) == 0


def test_gaplegs_main_calls_build_leg_when_file_missing(tmp_path, monkeypatch):
    """OUT 文件不存在时，main() 必须为全部 4 段调用 build_leg 并写出文件。"""
    out_path = tmp_path / "gap-legs.json"
    monkeypatch.setattr(gap_legs, "OUT", out_path)

    fake_build_leg, calls = _counting_build_leg()
    monkeypatch.setattr(gap_legs, "build_leg", fake_build_leg)

    gap_legs.main()

    assert set(calls) == set(LEG_IDS)
    assert out_path.exists()
    raw = out_path.read_text(encoding="utf-8")
    for lid in LEG_IDS:
        assert lid in raw


def test_gaplegs_main_calls_build_leg_when_file_incomplete(tmp_path, monkeypatch):
    """OUT 文件存在但缺某个 leg id 时，main() 必须至少为缺失的那段调用 build_leg。"""
    out_path = tmp_path / "gap-legs.json"
    partial = {
        lid: {"id": lid, "points": [[86.0, 27.0, 3000.0]], "source": "s"}
        for lid in LEG_IDS
        if lid != "pheriche-pangboche"
    }
    out_path.write_text(json.dumps(partial), encoding="utf-8")
    monkeypatch.setattr(gap_legs, "OUT", out_path)

    fake_build_leg, calls = _counting_build_leg()
    monkeypatch.setattr(gap_legs, "build_leg", fake_build_leg)

    gap_legs.main()

    assert len(calls) >= 1
    assert "pheriche-pangboche" in calls


def test_gaplegs_main_refresh_forces_recompute_even_when_complete(tmp_path, monkeypatch):
    """--refresh（refresh=True）时无论文件是否齐备都重抓全部 4 段。"""
    out_path = tmp_path / "gap-legs.json"
    existing = {lid: {"id": lid, "points": [[86.0, 27.0, 3000.0]], "source": "s"} for lid in LEG_IDS}
    out_path.write_text(json.dumps(existing), encoding="utf-8")
    monkeypatch.setattr(gap_legs, "OUT", out_path)

    fake_build_leg, calls = _counting_build_leg()
    monkeypatch.setattr(gap_legs, "build_leg", fake_build_leg)

    gap_legs.main(refresh=True)

    assert set(calls) == set(LEG_IDS)
