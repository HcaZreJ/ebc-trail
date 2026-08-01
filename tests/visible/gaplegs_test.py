"""tests/visible/gaplegs_test.py — 缺口路段补测（scripts/gap_legs.py）的样例测试。

覆盖 build_graph 建图、shortest_path 找路、build_leg 在 OSM 步道连通时的主路径。
更多边界、错误场景与 main() 的幂等行为见 tests/hidden/gaplegs_test.py。

一次网络请求都不发：build_graph / shortest_path 是纯函数，直接喂手写的
Overpass JSON 字典；build_leg 用 monkeypatch 替掉 gap_legs.subprocess.run
（Overpass 抓取的出口）与 gap_legs.fetch_elevations（SRTM 抓取的出口）。
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


def test_gaplegs_build_graph_connects_shared_node_across_ways():
    """两条 way 共享同一 node id 时应自动连通，边权等于相邻 geometry 点的 haversine 米数。"""
    overpass_json = _overpass_json(
        [
            (100, [(1, 27.80, 86.71), (2, 27.81, 86.72), (3, 27.82, 86.73)]),
            (101, [(3, 27.82, 86.73), (4, 27.83, 86.74), (5, 27.84, 86.75)]),
        ]
    )

    nodes, adj = gap_legs.build_graph(overpass_json)

    expected_coords = {
        1: (27.80, 86.71),
        2: (27.81, 86.72),
        3: (27.82, 86.73),
        4: (27.83, 86.74),
        5: (27.84, 86.75),
    }
    assert set(nodes.keys()) == set(expected_coords.keys())
    for node_id, coord in expected_coords.items():
        assert nodes[node_id] == pytest.approx(coord)

    # node 3 来自两条 way 的连接点，度数应为 2：邻居 2（来自 way100）与 4（来自 way101）
    neighbors_of_3 = dict(adj[3])
    assert set(neighbors_of_3) == {2, 4}
    assert neighbors_of_3[2] == pytest.approx(_haversine_m(27.82, 86.73, 27.81, 86.72), rel=1e-6)
    assert neighbors_of_3[4] == pytest.approx(_haversine_m(27.82, 86.73, 27.83, 86.74), rel=1e-6)


def test_gaplegs_shortest_path_finds_route_along_connected_chain():
    """在通过共享 node 连通的链状图上，Dijkstra 应找到起点到终点的完整路径，按顺序排列。"""
    overpass_json = _overpass_json(
        [
            (100, [(1, 27.80, 86.71), (2, 27.81, 86.72), (3, 27.82, 86.73)]),
            (101, [(3, 27.82, 86.73), (4, 27.83, 86.74), (5, 27.84, 86.75)]),
        ]
    )
    nodes, adj = gap_legs.build_graph(overpass_json)

    path = gap_legs.shortest_path(nodes, adj, 1, 5)

    assert path == [
        (27.80, 86.71),
        (27.81, 86.72),
        (27.82, 86.73),
        (27.83, 86.74),
        (27.84, 86.75),
    ]


def test_gaplegs_build_leg_uses_osm_path_when_connected(monkeypatch):
    """OSM 步道连通时，build_leg 取该步道的点序列，source 不出现「不连通」字样。"""
    start = (27.8054, 86.7124)
    goal = (27.8116, 86.7183)
    mid = (27.8085, 86.7150)
    overpass_json = _overpass_json([(1, [(1, *start), (2, *mid), (3, *goal)])])

    # gap_legs 内部对 subprocess.run 的调用被整体替换（raising=False：不强求当前就已
    # `import subprocess`，实现落地后同样生效，因为替换的是模块命名空间里的 "subprocess" 名字）。
    monkeypatch.setattr(
        gap_legs,
        "subprocess",
        types.SimpleNamespace(
            run=lambda *a, **k: types.SimpleNamespace(
                returncode=0, stdout=json.dumps(overpass_json), stderr=""
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        gap_legs, "fetch_elevations", lambda pts: [3000.0 + 10 * i for i in range(len(pts))]
    )

    leg = gap_legs.build_leg(
        "namche-everest-view",
        start=start,
        goal=goal,
        bbox=(86.70, 27.80, 86.72, 27.82),
        out_and_back=False,
    )

    assert leg["id"] == "namche-everest-view"
    assert "不连通" not in leg["source"]
    assert len(leg["points"]) == 3
    assert leg["points"][0] == pytest.approx([start[1], start[0], 3000.0], abs=1e-4)
    assert leg["points"][-1] == pytest.approx([goal[1], goal[0], 3020.0], abs=1e-4)
