"""T3「逐日轨迹装配与统计」的全面测试（day_tracks.py + route_points.py）。

覆盖：
- route_points.TREK_VILLAGES 的坐标校正、ACCLIMATIZE_POINTS、LOOP_LANDMARKS
  （事实依据：sources/15-kmz-loop-track.md 的标注点坐标表）
- day_tracks.stats() 的纯函数计算（distance_km / ascent_m / descent_m /
  start_ele_m / end_ele_m / source、行序）
- day_tracks.load_gpx() 的 GPX 解析
- day_tracks.load_gap_legs() 的 JSON 解析
- day_tracks.assemble() 的拼接逻辑（构造假输入的单元测试 + 真实 KML/GPX 的集成测试）
- day_tracks.main() 的产物写出

点的统一表示是 (lon, lat, ele)；route_points.TREK_VILLAGES 的元组是
(名称, lat, lon, 海拔)，两者字段顺序不同，测试里按各自约定读取。
"""
import csv
import json
import math
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import day_tracks  # noqa: E402
import geo  # noqa: E402
import kmz_loop  # noqa: E402
import route_points  # noqa: E402


# ---------------------------------------------------------------------------
# route_points 坐标校正
# ---------------------------------------------------------------------------

# sources/15 标注点表：9 个村庄在 KMZ 里有对应标注点，坐标应精确校正到这些值
# （容差 1e-4 度）。KMZ 名称与报告用名不一致的三处：Lukla airport→Lukla、
# Manjo→Monjo、Gorakshep→Gorak Shep。
KMZ_CORRECTED_COORDS = {
    "Lukla": (27.6882, 86.7315),
    "Phakding": (27.7392, 86.7122),
    "Monjo": (27.7701, 86.7238),
    "Namche": (27.8054, 86.7124),
    "Pangboche": (27.8547, 86.7908),
    "Dingboche": (27.8895, 86.8273),
    "Lobuche": (27.9478, 86.8104),
    "Gorak Shep": (27.9794, 86.8283),
    "EBC": (27.9986, 86.8489),
}

# 文献海拔口径不因坐标校正而改变（报告展示文献海拔，不展示 KMZ GPS 读数）。
LITERATURE_ELEVATIONS = {
    "Lukla": 2860,
    "Phakding": 2610,
    "Monjo": 2835,
    "Namche": 3440,
    "Tengboche": 3860,
    "Pangboche": 3930,
    "Dingboche": 4410,
    "Pheriche": 4280,
    "Lobuche": 4940,
    "Gorak Shep": 5164,
    "EBC": 5364,
}


@pytest.mark.parametrize("name,expected", list(KMZ_CORRECTED_COORDS.items()))
def test_daytracks_trek_villages_kmz_corrected_coordinates(name, expected):
    """9 个有 KMZ 标注点的村庄，(lat, lon) 应等于 sources/15 标注点表对应行（容差 1e-4 度）。"""
    villages = {n: (lat, lon) for n, lat, lon, _ in route_points.TREK_VILLAGES}
    assert name in villages, f"TREK_VILLAGES 缺少 {name}"
    lat, lon = villages[name]
    exp_lat, exp_lon = expected
    assert lat == pytest.approx(exp_lat, abs=1e-4)
    assert lon == pytest.approx(exp_lon, abs=1e-4)


def test_daytracks_trek_villages_non_kmz_points_use_given_values():
    """Tengboche 与 Pheriche 在 KMZ 里没有标注点，坐标用 sources/15 给定的值：
    Tengboche (27.8361, 86.7645)、Pheriche (27.8941, 86.8198，取自 OSM)。
    """
    villages = {n: (lat, lon) for n, lat, lon, _ in route_points.TREK_VILLAGES}
    ten_lat, ten_lon = villages["Tengboche"]
    assert ten_lat == pytest.approx(27.8361, abs=1e-4)
    assert ten_lon == pytest.approx(86.7645, abs=1e-4)
    phe_lat, phe_lon = villages["Pheriche"]
    assert phe_lat == pytest.approx(27.8941, abs=1e-4)
    assert phe_lon == pytest.approx(86.8198, abs=1e-4)


def test_daytracks_trek_villages_literature_elevation_unchanged():
    """坐标校正不改变文献海拔列；Namche 仍是 3440，不是 KMZ 记录的 3495。"""
    assert len(route_points.TREK_VILLAGES) == 11
    elevations = {n: ele for n, _, _, ele in route_points.TREK_VILLAGES}
    assert elevations == LITERATURE_ELEVATIONS
    assert elevations["Namche"] == 3440


def test_daytracks_acclimatize_points_two_entries_with_expected_elevations():
    """ACCLIMATIZE_POINTS 含两个海拔适应点：Everest View 观景台 3880m、Nangkartshang 5080m。"""
    points = route_points.ACCLIMATIZE_POINTS
    assert len(points) == 2
    elevations = {p[-1] for p in points}
    assert elevations == {3880, 5080}


def test_daytracks_loop_landmarks_eight_named_points_with_expected_elevations():
    """LOOP_LANDMARKS 含 8 个环线关键节点及其海拔（供地图标注）。"""
    expected = {
        "Kongma La": 5535,
        "Cho La": 5368,
        "Renjo La": 5411,
        "Gokyo": 4790,
        "Chukhung": 4740,
        "Chukhung Ri": 5546,
        "Dzongla": 4830,
        "Thame": 3860,
    }
    landmarks = {p[0]: p[-1] for p in route_points.LOOP_LANDMARKS}
    assert landmarks == expected


# ---------------------------------------------------------------------------
# day_tracks.stats —— 纯函数
# ---------------------------------------------------------------------------


def test_daytracks_stats_monotonic_ascent_day():
    """单调上升的一天：ascent 等于净高差，descent 为 0。"""
    pts = [
        (86.7315, 27.6869, 2610.0),
        (86.7300, 27.6900, 2660.0),
        (86.7280, 27.6950, 2720.0),
        (86.7250, 27.7000, 2790.0),
        (86.7200, 27.7100, 2860.0),
    ]
    row = day_tracks.stats({1: pts})[0]
    assert row["ascent_m"] == 250
    assert row["descent_m"] == 0
    assert row["start_ele_m"] == 2610
    assert row["end_ele_m"] == 2860


def test_daytracks_stats_up_then_down_day_both_positive():
    """先升后降的一天：ascent 与 descent 都为正数。"""
    pts = [
        (86.80, 27.90, 4700.0),
        (86.80, 27.91, 5000.0),
        (86.80, 27.92, 4700.0),
    ]
    row = day_tracks.stats({1: pts})[0]
    assert row["ascent_m"] > 0
    assert row["descent_m"] > 0


def test_daytracks_stats_distance_km_one_decimal_meridian():
    """沿固定经度（正南北）移动的距离可解析计算，distance_km 保留一位小数。

    haversine 在同经度时精确等于 R * Δlat（弧度），可据此算出预期值，
    不依赖具体实现细节。
    """
    lat0, lon0 = 27.9478, 86.8104
    pts = [(lon0, lat0 + i * 0.01, 4900.0 + i * 10.0) for i in range(5)]
    expected_km = 6371.0 * (0.04 * math.pi / 180.0)
    row = day_tracks.stats({1: pts})[0]
    assert row["distance_km"] == pytest.approx(round(expected_km, 1), abs=0.05)
    assert row["distance_km"] == round(row["distance_km"], 1)


def test_daytracks_stats_start_end_elevation_rounded():
    """start_ele_m / end_ele_m 取首末点海拔并取整。"""
    pts = [
        (86.70, 27.70, 2801.6),
        (86.71, 27.71, 2850.0),
        (86.72, 27.72, 2900.4),
    ]
    row = day_tracks.stats({1: pts})[0]
    assert row["start_ele_m"] == round(2801.6)
    assert row["end_ele_m"] == round(2900.4)


def test_daytracks_stats_row_count_and_sorted_by_day():
    """返回行数等于输入天数，按 day 升序排列，不受输入字典键序影响。"""
    pts = [
        (86.70, 27.70, 2800.0),
        (86.71, 27.71, 2850.0),
    ]
    tracks = {3: pts, 1: pts, 2: pts}
    rows = day_tracks.stats(tracks)
    assert len(rows) == 3
    assert [r["day"] for r in rows] == [1, 2, 3]


def test_daytracks_stats_source_field_present_and_nonempty():
    """每行都带 source 字段，记录该天用了哪些数据来源。"""
    pts = [
        (86.70, 27.70, 2800.0),
        (86.71, 27.71, 2850.0),
    ]
    row = day_tracks.stats({1: pts})[0]
    assert isinstance(row["source"], str)
    assert row["source"] != ""


# ---------------------------------------------------------------------------
# day_tracks.load_gpx
# ---------------------------------------------------------------------------

GPX_NS_URI = "http://www.topografix.com/GPX/1/1"


def _write_gpx(tmp_path, points, name="sample.gpx"):
    """写一个最小 GPX 文件，points = [(lat, lon, ele), ...]。"""
    trkpts = "\n".join(
        f'      <trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele></trkpt>'
        for lat, lon, ele in points
    )
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<gpx version="1.1" creator="test" xmlns="{GPX_NS_URI}">\n'
        f"  <trk><trkseg>\n{trkpts}\n  </trkseg></trk>\n"
        "</gpx>\n"
    )
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_daytracks_load_gpx_custom_fixture_point_order_and_fields(tmp_path):
    """自建 GPX 的点序保留输入顺序，字段转换为 (lon, lat, ele)。"""
    gpx_path = _write_gpx(
        tmp_path,
        [
            (27.6869, 86.7314, 2860.0),
            (27.7000, 86.7200, 2700.5),
            (27.7433, 86.7133, 2610),
        ],
    )
    pts = day_tracks.load_gpx(gpx_path)
    assert len(pts) == 3
    expected = [
        (86.7314, 27.6869, 2860.0),
        (86.7200, 27.7000, 2700.5),
        (86.7133, 27.7433, 2610.0),
    ]
    for (lon, lat, ele), (exp_lon, exp_lat, exp_ele) in zip(pts, expected):
        assert lon == pytest.approx(exp_lon, abs=1e-6)
        assert lat == pytest.approx(exp_lat, abs=1e-6)
        assert ele == pytest.approx(exp_ele, abs=1e-6)


def test_daytracks_load_gpx_empty_track_returns_empty_list(tmp_path):
    """没有 trkpt 的 GPX 文件返回空列表。"""
    gpx_path = _write_gpx(tmp_path, [])
    assert day_tracks.load_gpx(gpx_path) == []


def test_daytracks_load_gpx_real_asset_point_count_and_start():
    """真实 assets/Everest_Base_Camp.gpx 共 3291 个点，起点接近 Lukla
    (27.687, 86.732, 2855m)（见 TECHSTACK.md GPX 数据来源）。
    """
    pts = day_tracks.load_gpx()
    assert len(pts) == 3291
    lon0, lat0, ele0 = pts[0]
    assert lat0 == pytest.approx(27.687, abs=0.001)
    assert lon0 == pytest.approx(86.732, abs=0.001)
    assert ele0 == pytest.approx(2855, abs=5)


# ---------------------------------------------------------------------------
# day_tracks.load_gap_legs
# ---------------------------------------------------------------------------


def test_daytracks_load_gap_legs_parses_json_fixture(tmp_path):
    """磁盘结构是 {leg_id: {"points": [[lon, lat, ele], ...], "source": str}}，
    解析后只留 points，输出 {leg_id: [(lon, lat, ele), ...]}。"""
    gap_path = tmp_path / "gap-legs.json"
    gap_path.write_text(
        json.dumps(
            {
                "leg-a": {
                    "points": [[86.71, 27.81, 3500.0], [86.72, 27.82, 3520.5]],
                    "source": "OSM+SRTM30m",
                },
                "leg-b": {
                    "points": [[86.80, 27.90, 4800.0]],
                    "source": "OSM 步道不连通，按直线采样 SRTM30m",
                },
            }
        ),
        encoding="utf-8",
    )
    legs = day_tracks.load_gap_legs(gap_path)
    assert set(legs.keys()) == {"leg-a", "leg-b"}
    assert legs["leg-a"] == [(86.71, 27.81, 3500.0), (86.72, 27.82, 3520.5)]
    assert legs["leg-b"] == [(86.80, 27.90, 4800.0)]


def test_daytracks_load_gap_legs_drops_source_field(tmp_path):
    """source 字段不进返回值：每段的值是纯点序列，不是带元数据的字典。"""
    gap_path = tmp_path / "gap-legs.json"
    gap_path.write_text(
        json.dumps({"leg-a": {"points": [[86.71, 27.81, 3500.0]], "source": "OSM+SRTM30m"}}),
        encoding="utf-8",
    )
    legs = day_tracks.load_gap_legs(gap_path)
    assert legs["leg-a"] == [(86.71, 27.81, 3500.0)]
    assert not isinstance(legs["leg-a"], dict)


# ---------------------------------------------------------------------------
# day_tracks.assemble —— 构造假输入的单元测试
# ---------------------------------------------------------------------------

# 端点精确落在真实村庄坐标上：这样 geo.slice_between 的最近点匹配是距离 0 的
# 精确命中，测试结果不依赖 geo 实现的具体数值精度，只依赖其契约（最近点、
# 方向总是 a→b）。
LUKLA = (27.6882, 86.7315)
PHAKDING = (27.7392, 86.7122)
NAMCHE = (27.8054, 86.7124)
TENGBOCHE = (27.8361, 86.7645)
PANGBOCHE = (27.8547, 86.7908)
DINGBOCHE = (27.8895, 86.8273)
PHERICHE = (27.8941, 86.8198)
LOBUCHE = (27.9478, 86.8104)
GORAKSHEP = (27.9794, 86.8283)
EBC_PT = (27.9986, 86.8489)
KALA_PATTHAR_PT = (27.9950, 86.8287)
EVEREST_VIEW = (27.8116, 86.7183)
NANGKARTSHANG = (27.9055, 86.8355)


def _lerp_segment(a, b, n, ele_a, ele_b):
    """a→b 之间线性插值 n 个点（含首尾），a/b = (lat, lon)，返回 [(lon, lat, ele)]。"""
    lat_a, lon_a = a
    lat_b, lon_b = b
    pts = []
    for i in range(n):
        t = i / (n - 1)
        lat = lat_a + (lat_b - lat_a) * t
        lon = lon_a + (lon_b - lon_a) * t
        ele = ele_a + (ele_b - ele_a) * t
        pts.append((lon, lat, ele))
    return pts


def _placeholder_segment(seed):
    """跟真实村庄坐标远离的占位线，assemble() 的拼接表不会用到它们。"""
    base = 0.001 * seed
    return [(base, base, 0.0), (base + 0.01, base + 0.01, 10.0)]


def _build_fake_inputs():
    """构造 20 条假 KMZ 线 + 假 GPX + 4 段假补测，覆盖 assemble() 拼接表用到的
    全部下标（K5,K6,K7,K8,K12,K13,K18）与 4 个 leg id。

    返回 (lines, gpx, legs, components)，components 记录 D5/D8/D9/D10 各自
    由哪两段拼成，供之后跟 assemble() 的结果比对点数。
    """
    lines = [None] * 20
    for i in range(20):
        lines[i] = _placeholder_segment(i)

    lines[5] = _lerp_segment(LUKLA, PHAKDING, 8, 2860, 2610)
    lines[6] = _lerp_segment(PHAKDING, NAMCHE, 10, 2610, 3440)

    seg7a = _lerp_segment(NAMCHE, TENGBOCHE, 8, 3440, 3860)
    seg7b = _lerp_segment(TENGBOCHE, PANGBOCHE, 8, 3860, 3930)
    lines[7] = seg7a + seg7b[1:]

    lines[8] = _lerp_segment(PANGBOCHE, DINGBOCHE, 8, 3930, 4410)

    seg12a = _lerp_segment(GORAKSHEP, EBC_PT, 6, 5164, 5364)
    seg12b = _lerp_segment(EBC_PT, GORAKSHEP, 6, 5364, 5164)
    lines[12] = seg12a + seg12b[1:]

    seg13a = _lerp_segment(GORAKSHEP, KALA_PATTHAR_PT, 6, 5164, 5601)
    seg13b = _lerp_segment(KALA_PATTHAR_PT, GORAKSHEP, 6, 5601, 5164)
    seg13c = _lerp_segment(GORAKSHEP, LOBUCHE, 6, 5164, 4932)
    lines[13] = seg13a + seg13b[1:] + seg13c[1:]

    lines[18] = _lerp_segment(NAMCHE, LUKLA, 10, 3440, 2860)

    gseg1 = _lerp_segment(NAMCHE, PANGBOCHE, 8, 3440, 3930)
    gseg2 = _lerp_segment(PANGBOCHE, DINGBOCHE, 8, 3930, 4410)
    gseg3 = _lerp_segment(DINGBOCHE, LOBUCHE, 10, 4410, 4932)
    gseg4 = _lerp_segment(LOBUCHE, GORAKSHEP, 10, 4932, 5164)
    gpx = gseg1 + gseg2[1:] + gseg3[1:] + gseg4[1:]

    leg_ev = _lerp_segment(NAMCHE, EVEREST_VIEW, 6, 3440, 3880)
    leg_dn = _lerp_segment(DINGBOCHE, NANGKARTSHANG, 6, 4410, 5080)
    leg_lp = _lerp_segment(LOBUCHE, PHERICHE, 8, 4932, 4280)
    leg_pp = _lerp_segment(PHERICHE, PANGBOCHE, 8, 4280, 3930)
    legs = {
        "namche-everest-view": leg_ev + list(reversed(leg_ev))[1:],
        "dingboche-nangkartshang": leg_dn + list(reversed(leg_dn))[1:],
        "lobuche-pheriche": leg_lp,
        "pheriche-pangboche": leg_pp,
    }

    components = {
        5: [seg7b, lines[8]],
        8: [gseg4, lines[12]],
        9: [lines[13], legs["lobuche-pheriche"]],
        10: [legs["pheriche-pangboche"], list(reversed(gseg1))],
    }
    return lines, gpx, legs, components


def test_daytracks_assemble_returns_days_1_to_11_only():
    """assemble() 的 key 恰好是 1..11；Day 12（转场日）不进字典。"""
    lines, gpx, legs, _ = _build_fake_inputs()
    tracks = day_tracks.assemble(lines, gpx, legs)
    assert set(tracks.keys()) == set(range(1, 12))


def test_daytracks_assemble_points_nonempty_and_are_three_tuples():
    """每天的点序列非空，且每个点都是 (lon, lat, ele) 三元组。"""
    lines, gpx, legs, _ = _build_fake_inputs()
    tracks = day_tracks.assemble(lines, gpx, legs)
    for day, pts in tracks.items():
        assert len(pts) > 0, f"day {day} 轨迹为空"
        for p in pts:
            assert len(p) == 3


@pytest.mark.parametrize("day", [5, 8, 9, 10])
def test_daytracks_assemble_multi_segment_days_exceed_each_component(day):
    """D5/D8/D9/D10 是两段拼接而成，装配后（重采样后）的点数应大于它任一单段
    单独重采样后的点数——因为拼接后总里程严格大于任一单段的里程，
    固定步长重采样的点数随里程单调不减。
    """
    lines, gpx, legs, components = _build_fake_inputs()
    tracks = day_tracks.assemble(lines, gpx, legs)
    combined_len = len(tracks[day])
    for seg in components[day]:
        seg_len = len(geo.resample(seg, day_tracks.RESAMPLE_STEP_M))
        assert combined_len > seg_len


def test_daytracks_assemble_real_kml_gpx_distances_and_elevations():
    """用真实 KML 导航线（kmz_loop.load_lines）与真实 GPX（day_tracks.load_gpx）
    装配，D1/D2/D11 的里程与 D7 的起终点海拔落在合理容差内。

    D1 (Lukla→Phakding, K5 整条) 对应 sources/15 的 L5 = 8.3 km。
    D2 (Phakding→Namche, K6 整条) 对应 L6 = 11.9 km。
    D11 (Namche→Lukla, K18 切片) 是 L18(25.5km) 的子段，落在 18-20 km。
    D7 (Dingboche→Lobuche, GPX 切片) 起点海拔约 4300m、终点约 4930m。
    legs 用构造的假段（真实 data/gap-legs.json 尚不存在），
    D3/D6/D9/D10 不在本用例的断言范围内。
    """
    lines = kmz_loop.load_lines()
    gpx = day_tracks.load_gpx()
    _, _, legs, _ = _build_fake_inputs()
    tracks = day_tracks.assemble(lines, gpx, legs)
    rows = {r["day"]: r for r in day_tracks.stats(tracks)}

    assert rows[1]["distance_km"] == pytest.approx(8.3, rel=0.15)
    assert rows[2]["distance_km"] == pytest.approx(11.9, rel=0.15)

    d11 = rows[11]["distance_km"]
    assert 18 * 0.85 <= d11 <= 20 * 1.15

    assert rows[7]["start_ele_m"] == pytest.approx(4300, abs=60)
    assert rows[7]["end_ele_m"] == pytest.approx(4930, abs=60)


# ---------------------------------------------------------------------------
# day_tracks.main
# ---------------------------------------------------------------------------


def test_daytracks_main_writes_tracks_json_and_stats_csv(tmp_path, monkeypatch):
    """main() 写出两个产物文件；CSV 表头与 JSON 的 key 形态符合契约。"""
    fake_tracks = {
        1: [(86.7315, 27.6882, 2860.0), (86.7122, 27.7392, 2610.0)],
        2: [(86.7122, 27.7392, 2610.0), (86.7124, 27.8054, 3440.0)],
    }
    tracks_out = tmp_path / "day-tracks.json"
    stats_out = tmp_path / "day-track-stats.csv"
    monkeypatch.setattr(day_tracks, "TRACKS_OUT", tracks_out)
    monkeypatch.setattr(day_tracks, "STATS_OUT", stats_out)
    monkeypatch.setattr(day_tracks, "assemble", lambda *a, **k: fake_tracks)

    day_tracks.main()

    assert tracks_out.exists()
    assert stats_out.exists()

    written = json.loads(tracks_out.read_text(encoding="utf-8"))
    assert set(written.keys()) == {"1", "2"}

    with open(stats_out, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == [
        "day",
        "distance_km",
        "ascent_m",
        "descent_m",
        "start_ele_m",
        "end_ele_m",
        "source",
    ]

    with open(stats_out, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert {r["day"] for r in rows} == {"1", "2"}


def test_daytracks_main_rounds_coordinates_and_elevation(tmp_path, monkeypatch):
    """day-tracks.json 的坐标写 6 位小数、海拔写 1 位小数。"""
    lon, lat, ele = 86.712345678, 27.739212345, 2610.44444
    fake_tracks = {1: [(lon, lat, ele), (86.71, 27.74, 2600.0)]}
    tracks_out = tmp_path / "day-tracks.json"
    stats_out = tmp_path / "day-track-stats.csv"
    monkeypatch.setattr(day_tracks, "TRACKS_OUT", tracks_out)
    monkeypatch.setattr(day_tracks, "STATS_OUT", stats_out)
    monkeypatch.setattr(day_tracks, "assemble", lambda *a, **k: fake_tracks)

    day_tracks.main()

    written = json.loads(tracks_out.read_text(encoding="utf-8"))
    got_lon, got_lat, got_ele = written["1"][0]
    assert got_lon == pytest.approx(round(lon, 6), abs=1e-9)
    assert got_lat == pytest.approx(round(lat, 6), abs=1e-9)
    assert got_ele == pytest.approx(round(ele, 1), abs=1e-9)
