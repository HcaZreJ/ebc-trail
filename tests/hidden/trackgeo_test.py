"""tests/hidden/trackgeo_test.py

work unit T1「几何工具与 KMZ 解析」的全面契约测试，覆盖
scripts/geo.py 的 haversine_m / cum_km / resample / smooth_ele / gain_loss /
nearest_index / slice_between，以及 scripts/kmz_loop.py 的 load_lines / load_waypoints。

坐标顺序约定：轨迹点是 (lon, lat, ele) 三元组；haversine_m / nearest_index /
slice_between 的参数是 lat, lon 顺序。

一些期望值用一个独立于被测模块的参考 haversine 实现（标准公式，R=6371000 m）
在测试内现算，避免手工推导时引入算术错误。
"""
import math
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import geo  # noqa: E402
import kmz_loop  # noqa: E402

KML_PATH = ROOT / "assets" / "ebc-loop.kml"
KML_NS = "http://www.opengis.net/kml/2.2"


def _ref_haversine_m(lat1, lon1, lat2, lon2):
    """独立的参考 haversine 实现（标准公式，R=6371000 m），用于推导期望值。"""
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _kml(body):
    """拼一份最小合法的 KML 2.2 文档，body 是 Document 内部的 XML 片段。"""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<kml xmlns="{KML_NS}">\n'
        "  <Document>\n"
        f"{body}\n"
        "  </Document>\n"
        "</kml>\n"
    )


def _six_pts():
    """沿同一经线的 6 个点，供 slice_between 测试使用。"""
    return [(0.0, 0.001 * i, 1000.0 + i * 5) for i in range(6)]


# ---------------------------------------------------------------------------
# geo.haversine_m
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lat, lon",
    [(0.0, 0.0), (27.8054, 86.7124), (-33.8688, 151.2093)],
    ids=["origin", "namche", "southern-hemisphere"],
)
def test_trackgeo_haversine_m_same_point_returns_zero(lat, lon):
    """同一点距离恒为 0.0，无论坐标落在哪个象限。"""
    assert geo.haversine_m(lat, lon, lat, lon) == pytest.approx(0.0, abs=1e-9)


def test_trackgeo_haversine_m_known_distance_between_two_points():
    """Namche 到 Everest View 观景台的大圆距离，用标准公式手算约 901.12 m。"""
    dist = geo.haversine_m(27.8054, 86.7124, 27.8116, 86.7183)
    assert dist == pytest.approx(901.118013138276, abs=1.0)


def test_trackgeo_haversine_m_matches_one_degree_latitude():
    """沿同一经线纬度相差 1 度，大圆距离精确等于 R * (pi/180)，约 111.195 km。"""
    dist = geo.haversine_m(0.0, 0.0, 1.0, 0.0)
    assert dist == pytest.approx(111194.92664455874, abs=1.0)


def test_trackgeo_haversine_m_is_symmetric():
    """交换两点顺序距离不变。"""
    a = (10.0, 20.0)
    b = (15.5, 25.5)
    assert geo.haversine_m(a[0], a[1], b[0], b[1]) == pytest.approx(
        geo.haversine_m(b[0], b[1], a[0], a[1]), rel=1e-9
    )


# ---------------------------------------------------------------------------
# geo.cum_km
# ---------------------------------------------------------------------------


def test_trackgeo_cum_km_empty_returns_empty_list():
    """空序列返回 []。"""
    assert geo.cum_km([]) == []


def test_trackgeo_cum_km_single_point_returns_zero():
    """单点返回 [0.0]。"""
    result = geo.cum_km([(86.0, 27.0, 3000.0)])
    assert result == pytest.approx([0.0])


def test_trackgeo_cum_km_multi_point_matches_reference_distance():
    """逐点累加 haversine：与独立参考实现算出的累计公里数一致，首元素为 0.0。"""
    lats = [0.0, 0.001, 0.002, 0.0035, 0.006]
    pts = [(0.0, lat, 2000.0 + i * 10) for i, lat in enumerate(lats)]

    expected_km = [0.0]
    total_m = 0.0
    for i in range(1, len(lats)):
        total_m += _ref_haversine_m(lats[i - 1], 0.0, lats[i], 0.0)
        expected_km.append(total_m / 1000.0)

    result = geo.cum_km(pts)

    assert len(result) == len(pts)
    assert result[0] == pytest.approx(0.0)
    for got, exp in zip(result, expected_km):
        assert got == pytest.approx(exp, abs=1e-4)


# ---------------------------------------------------------------------------
# geo.resample
# ---------------------------------------------------------------------------


def test_trackgeo_resample_linear_interpolation_along_meridian():
    """两点间距精确 200 m、step=50 m：沿经线线性插值出 5 个等距点，
    海拔（2000 -> 2400）随位置同步线性插值。"""
    lat1 = 0.0017986432118374611  # 对应精确 200 m 纬度差（R=6371000）
    pts = [(0.0, 0.0, 2000.0), (0.0, lat1, 2400.0)]

    result = geo.resample(pts, step_m=50.0)

    expected = [
        (0.0, 0.0, 2000.0),
        (0.0, 0.0004496608029593653, 2100.0),
        (0.0, 0.0008993216059187306, 2200.0),
        (0.0, 0.0013489824088780957, 2300.0),
        (0.0, lat1, 2400.0),
    ]

    assert len(result) == len(expected)
    for got, exp in zip(result, expected):
        assert got[0] == pytest.approx(exp[0], abs=1e-6)
        assert got[1] == pytest.approx(exp[1], abs=1e-6)
        assert got[2] == pytest.approx(exp[2], abs=0.5)


@pytest.mark.parametrize("step_m", [0, -5, -0.001], ids=["zero", "negative", "tiny-negative"])
def test_trackgeo_resample_step_le_zero_raises_value_error(step_m):
    """step_m <= 0 时抛 ValueError。"""
    pts = [(0.0, 0.0, 2000.0), (0.0, 0.01, 2100.0)]
    with pytest.raises(ValueError):
        geo.resample(pts, step_m=step_m)


@pytest.mark.parametrize(
    "pts",
    [[], [(86.0, 27.0, 3000.0)]],
    ids=["empty", "single-point"],
)
def test_trackgeo_resample_fewer_than_two_points_returned_unchanged(pts):
    """pts 少于 2 个点时原样返回。"""
    result = geo.resample(pts, step_m=25.0)
    assert list(result) == pts


def test_trackgeo_resample_segment_spacing_stays_within_step_bound():
    """多段轨迹重采样后，首尾必定保留；相邻输出点间距不应远超 step_m
    （允许因端点吸附/取整有一定余量，但不应出现远超 step 的大跳变）。"""
    lats = [0.0, 0.0020, 0.0045]  # 每段都明显大于 step_m
    pts = [(0.0, lat, 2000.0 + i * 50) for i, lat in enumerate(lats)]
    step_m = 40.0

    result = geo.resample(pts, step_m=step_m)

    assert result[0][0] == pytest.approx(pts[0][0], abs=1e-9)
    assert result[0][1] == pytest.approx(pts[0][1], abs=1e-9)
    assert result[-1][0] == pytest.approx(pts[-1][0], abs=1e-9)
    assert result[-1][1] == pytest.approx(pts[-1][1], abs=1e-9)
    assert len(result) > len(pts)

    for i in range(len(result) - 1):
        lon_a, lat_a, _ = result[i]
        lon_b, lat_b, _ = result[i + 1]
        dist = _ref_haversine_m(lat_a, lon_a, lat_b, lon_b)
        assert 0.0 <= dist <= step_m * 1.5


# ---------------------------------------------------------------------------
# geo.smooth_ele
# ---------------------------------------------------------------------------


def test_trackgeo_smooth_ele_removes_isolated_spike():
    """滚动中位数压掉 GPS 单点跳变：孤立尖峰被完全吃掉。"""
    eles = [10.0, 10.0, 100.0, 10.0, 10.0]
    result = geo.smooth_ele(eles, window=3)
    assert list(result) == pytest.approx([10.0, 10.0, 10.0, 10.0, 10.0])


def test_trackgeo_smooth_ele_edges_shrink_without_padding():
    """两端窗口收缩而不是补零/补边：window=3 时首尾窗口只有 2 个元素，
    中位数因而是非整数，证明没有做 padding。"""
    eles = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = geo.smooth_ele(eles, window=3)
    assert list(result) == pytest.approx([1.5, 2.0, 3.0, 4.0, 4.5])


def test_trackgeo_smooth_ele_window_one_returns_original():
    """window=1 时原样返回。"""
    eles = [5.0, 3.0, 9.0, 1.0, 7.0]
    result = geo.smooth_ele(eles, window=1)
    assert list(result) == pytest.approx(eles)


def test_trackgeo_smooth_ele_even_window_uses_same_radius_as_next_odd():
    """window 为偶数时按 window//2 取半径：window=4 与 window=5 的半径相同（都是 2），
    因此对同一序列产生相同的输出。"""
    eles = [5.0, 1.0, 4.0, 2.0, 8.0, 3.0, 9.0, 6.0]
    result_even = geo.smooth_ele(eles, window=4)
    result_odd = geo.smooth_ele(eles, window=5)
    assert list(result_even) == pytest.approx(list(result_odd))


def test_trackgeo_smooth_ele_window_larger_than_series_uses_whole_series_median():
    """window 大于序列长度时，每个位置的窗口都收缩成整条序列，输出全部等于整体中位数。"""
    eles = [1.0, 2.0, 3.0, 100.0, 5.0]
    result = geo.smooth_ele(eles, window=9)
    assert list(result) == pytest.approx([3.0, 3.0, 3.0, 3.0, 3.0])


def test_trackgeo_smooth_ele_empty_returns_empty():
    """空序列返回等长（空）序列。"""
    assert list(geo.smooth_ele([], window=9)) == []


# ---------------------------------------------------------------------------
# geo.gain_loss
# ---------------------------------------------------------------------------


def test_trackgeo_gain_loss_monotonic_increasing_small_steps():
    """单调上升序列（哪怕单步远小于 hyst）返回 (末-首, 0)。"""
    eles = [1000.0 + 2.0 * i for i in range(60)]
    ascent, descent = geo.gain_loss(eles, hyst=8.0)
    assert ascent == pytest.approx(eles[-1] - eles[0], abs=1e-6)
    assert descent == pytest.approx(0.0, abs=1e-6)


def test_trackgeo_gain_loss_monotonic_decreasing_small_steps():
    """单调下降序列返回 (0, 首-末)。"""
    eles = [1118.0 - 2.0 * i for i in range(60)]
    ascent, descent = geo.gain_loss(eles, hyst=8.0)
    assert ascent == pytest.approx(0.0, abs=1e-6)
    assert descent == pytest.approx(eles[0] - eles[-1], abs=1e-6)


def test_trackgeo_gain_loss_fluctuations_below_hysteresis_are_ignored():
    """全部波动都小于 hyst（整体极差 4 < hyst 8）时返回 (0, 0)。"""
    eles = [100.0, 102.0, 101.0, 104.0, 100.0, 103.0, 101.0]
    assert geo.gain_loss(eles, hyst=8.0) == pytest.approx((0.0, 0.0))


def test_trackgeo_gain_loss_confirms_swings_that_exceed_hysteresis():
    """明显超过 hyst 的往复波动（+100 / -150 / +50，hyst=8）应分别计入
    总爬升与总下降：ascent=150、descent=150。"""
    eles = [1000.0, 1100.0, 950.0, 1000.0]
    ascent, descent = geo.gain_loss(eles, hyst=8.0)
    assert ascent == pytest.approx(150.0, abs=1e-6)
    assert descent == pytest.approx(150.0, abs=1e-6)


def test_trackgeo_gain_loss_single_point_is_zero():
    """单点序列没有任何变化，返回 (0, 0)。"""
    assert geo.gain_loss([100.0], hyst=8.0) == pytest.approx((0.0, 0.0))


# ---------------------------------------------------------------------------
# geo.nearest_index
# ---------------------------------------------------------------------------


def test_trackgeo_nearest_index_exact_match_returns_zero_distance():
    """查询坐标与某个点完全一致时，返回该点索引与距离 0。"""
    pts = [(0.0, 0.001 * i, 2500.0 + i * 100) for i in range(5)]
    idx, dist = geo.nearest_index(pts, lat=0.003, lon=0.0)
    assert idx == 3
    assert dist == pytest.approx(0.0, abs=1e-6)


def test_trackgeo_nearest_index_picks_closest_point_by_distance():
    """线性扫描取 haversine 最近的点：查询点更靠近 idx3 而不是 idx4。"""
    pts = [(0.0, 0.001 * i, 2500.0 + i * 100) for i in range(5)]
    idx, dist = geo.nearest_index(pts, lat=0.0034, lon=0.0)
    expected_dist = _ref_haversine_m(0.0034, 0.0, 0.003, 0.0)
    assert idx == 3
    assert dist == pytest.approx(expected_dist, abs=0.5)


# ---------------------------------------------------------------------------
# geo.slice_between
# ---------------------------------------------------------------------------


def test_trackgeo_slice_between_forward_order():
    """a 的索引小于 b 的索引时，正常顺序返回，含首含尾。"""
    pts = _six_pts()
    result = geo.slice_between(pts, a=(0.002, 0.0), b=(0.005, 0.0))
    assert result == pytest.approx(pts[2:6])


def test_trackgeo_slice_between_reversed_when_a_is_after_b():
    """a 的索引大于 b 的索引时，结果反向，使返回序列总是从 a 走向 b。"""
    pts = _six_pts()
    result = geo.slice_between(pts, a=(0.005, 0.0), b=(0.002, 0.0))
    assert result == pytest.approx(list(reversed(pts[2:6])))


def test_trackgeo_slice_between_same_snap_index_returns_single_point():
    """两端点吸附到同一索引时，返回该单点组成的长度 1 序列。"""
    pts = _six_pts()
    result = geo.slice_between(pts, a=(0.003, 0.0), b=(0.003, 0.0))
    assert result == pytest.approx([pts[3]])


# ---------------------------------------------------------------------------
# kmz_loop.load_lines —— 真实资产
# ---------------------------------------------------------------------------


def test_trackgeo_load_lines_real_asset_has_twenty_lines_and_total_points():
    """真实 ebc-loop.kml 的导航线文件夹恰好 20 条 LineString，总点数 17377。"""
    lines = kmz_loop.load_lines(kml_path=str(KML_PATH))
    assert len(lines) == 20
    assert sum(len(line) for line in lines) == 17377


def test_trackgeo_load_lines_real_asset_preserves_appearance_order():
    """返回顺序 = 文件中出现顺序：第一条线的第一个点应是文件里第一条
    LineString 的第一个坐标三元组。"""
    lines = kmz_loop.load_lines(kml_path=str(KML_PATH))
    first_point = lines[0][0]
    assert first_point[0] == pytest.approx(86.713448, abs=1e-5)
    assert first_point[1] == pytest.approx(27.632987, abs=1e-5)
    assert first_point[2] == pytest.approx(2869.091771, abs=1e-2)


def test_trackgeo_load_lines_default_kml_path_uses_repo_asset():
    """kml_path 缺省时读仓库自带的 assets/ebc-loop.kml。"""
    old_cwd = os.getcwd()
    os.chdir(str(ROOT))
    try:
        lines = kmz_loop.load_lines()
    finally:
        os.chdir(old_cwd)
    assert len(lines) == 20


# ---------------------------------------------------------------------------
# kmz_loop.load_lines —— 自建小 KML 夹具
# ---------------------------------------------------------------------------


def test_trackgeo_load_lines_only_collects_target_folder(tmp_path):
    """LineString 只从 name 含「导航线」的 Folder 里收集，其它 Folder 里的线不计入。"""
    body = """
    <Folder>
      <name>导航线</name>
      <Placemark>
        <LineString>
          <coordinates>86.0,27.0,3000 86.001,27.001,3010</coordinates>
        </LineString>
      </Placemark>
    </Folder>
    <Folder>
      <name>其它轨迹</name>
      <Placemark>
        <LineString>
          <coordinates>10.0,10.0,100 10.001,10.001,110</coordinates>
        </LineString>
      </Placemark>
    </Folder>
    """
    kml_file = tmp_path / "sample.kml"
    kml_file.write_text(_kml(body), encoding="utf-8")

    lines = kmz_loop.load_lines(kml_path=str(kml_file))

    assert len(lines) == 1
    assert lines[0][0] == pytest.approx((86.0, 27.0, 3000.0))
    assert lines[0][1] == pytest.approx((86.001, 27.001, 3010.0))


def test_trackgeo_load_lines_matches_folder_name_containing_keyword(tmp_path):
    """Folder 名字只要包含「导航线」子串就命中，不要求完全相等。"""
    body = """
    <Folder>
      <name>2024 导航线 v2</name>
      <Placemark>
        <LineString>
          <coordinates>86.0,27.0,3000 86.001,27.001,3010</coordinates>
        </LineString>
      </Placemark>
    </Folder>
    """
    kml_file = tmp_path / "sample.kml"
    kml_file.write_text(_kml(body), encoding="utf-8")

    lines = kmz_loop.load_lines(kml_path=str(kml_file))

    assert len(lines) == 1


def test_trackgeo_load_lines_preserves_multi_placemark_order(tmp_path):
    """多条 LineString 时，按 Placemark 在文件里的出现顺序返回，各自点数正确。"""
    body = """
    <Folder>
      <name>导航线</name>
      <Placemark>
        <LineString><coordinates>1.0,1.0,100 1.1,1.1,110</coordinates></LineString>
      </Placemark>
      <Placemark>
        <LineString><coordinates>2.0,2.0,200 2.1,2.1,210 2.2,2.2,220</coordinates></LineString>
      </Placemark>
    </Folder>
    """
    kml_file = tmp_path / "sample.kml"
    kml_file.write_text(_kml(body), encoding="utf-8")

    lines = kmz_loop.load_lines(kml_path=str(kml_file))

    assert len(lines) == 2
    assert len(lines[0]) == 2
    assert len(lines[1]) == 3
    assert lines[1][2] == pytest.approx((2.2, 2.2, 220.0))


# ---------------------------------------------------------------------------
# kmz_loop.load_waypoints —— 真实资产
# ---------------------------------------------------------------------------


def test_trackgeo_load_waypoints_real_asset_known_names_present():
    """真实资产的标注点里含有报告用到的关键地名。"""
    waypoints = kmz_loop.load_waypoints(kml_path=str(KML_PATH))
    for name in (
        "Lukla airport",
        "Namche",
        "Gorakshep",
        "Kala Patthar",
        "Cho La Pass",
        "Renjo Pass",
    ):
        assert name in waypoints


def test_trackgeo_load_waypoints_real_asset_namche_coordinates():
    """Namche 标注点坐标与 KML 里 <Point><coordinates> 的实测值一致。"""
    waypoints = kmz_loop.load_waypoints(kml_path=str(KML_PATH))
    lat, lon, ele = waypoints["Namche"]
    assert lat == pytest.approx(27.805417, abs=1e-4)
    assert lon == pytest.approx(86.712387, abs=1e-4)
    assert ele == pytest.approx(3494.533113, abs=1.0)


def test_trackgeo_load_waypoints_real_asset_duplicate_keeps_first():
    """真实资产里「检查站」这个名字出现 3 次，返回值应等于文件中第一次出现的坐标。"""
    waypoints = kmz_loop.load_waypoints(kml_path=str(KML_PATH))
    assert "检查站" in waypoints
    lat, lon, ele = waypoints["检查站"]
    assert lat == pytest.approx(27.773722, abs=1e-4)
    assert lon == pytest.approx(86.722388, abs=1e-4)
    assert ele == pytest.approx(2859.933313, abs=1.0)


# ---------------------------------------------------------------------------
# kmz_loop.load_waypoints —— 自建小 KML 夹具
# ---------------------------------------------------------------------------


def test_trackgeo_load_waypoints_strips_cdata_name(tmp_path):
    """CDATA 包裹的名称要脱掉 CDATA，字典键是纯文本。"""
    body = """
    <Folder>
      <name><![CDATA[标注点]]></name>
      <Placemark>
        <name><![CDATA[Test Village]]></name>
        <Point><coordinates>86.7,27.8,3000</coordinates></Point>
      </Placemark>
    </Folder>
    """
    kml_file = tmp_path / "sample.kml"
    kml_file.write_text(_kml(body), encoding="utf-8")

    waypoints = kmz_loop.load_waypoints(kml_path=str(kml_file))

    assert "Test Village" in waypoints
    assert all("CDATA" not in name for name in waypoints)
    lat, lon, ele = waypoints["Test Village"]
    assert (lat, lon, ele) == pytest.approx((27.8, 86.7, 3000.0))


def test_trackgeo_load_waypoints_skips_empty_names(tmp_path):
    """名称为空的点跳过，不出现在返回字典里，也不影响其它点的解析。"""
    body = """
    <Folder>
      <name>标注点</name>
      <Placemark>
        <name></name>
        <Point><coordinates>86.71,27.81,3001</coordinates></Point>
      </Placemark>
      <Placemark>
        <name>Kept Point</name>
        <Point><coordinates>86.72,27.82,3002</coordinates></Point>
      </Placemark>
    </Folder>
    """
    kml_file = tmp_path / "sample.kml"
    kml_file.write_text(_kml(body), encoding="utf-8")

    waypoints = kmz_loop.load_waypoints(kml_path=str(kml_file))

    assert len(waypoints) == 1
    assert "Kept Point" in waypoints


def test_trackgeo_load_waypoints_dedup_keeps_first(tmp_path):
    """同名重复时保留第一个出现的坐标，忽略后续同名点。"""
    body = """
    <Folder>
      <name>标注点</name>
      <Placemark>
        <name>Camp</name>
        <Point><coordinates>86.70,27.80,3000</coordinates></Point>
      </Placemark>
      <Placemark>
        <name>Camp</name>
        <Point><coordinates>86.90,27.90,3500</coordinates></Point>
      </Placemark>
    </Folder>
    """
    kml_file = tmp_path / "sample.kml"
    kml_file.write_text(_kml(body), encoding="utf-8")

    waypoints = kmz_loop.load_waypoints(kml_path=str(kml_file))

    assert len(waypoints) == 1
    lat, lon, ele = waypoints["Camp"]
    assert (lat, lon, ele) == pytest.approx((27.80, 86.70, 3000.0))


def test_trackgeo_load_waypoints_ignores_non_target_folder(tmp_path):
    """标注点只从 name 含「标注点」的 Folder 收集，其它 Folder 里的命名点不计入。"""
    body = """
    <Folder>
      <name>标注点</name>
      <Placemark>
        <name>InFolder</name>
        <Point><coordinates>86.1,27.1,3000</coordinates></Point>
      </Placemark>
    </Folder>
    <Folder>
      <name>照片</name>
      <Placemark>
        <name>OutFolder</name>
        <Point><coordinates>86.2,27.2,3000</coordinates></Point>
      </Placemark>
    </Folder>
    """
    kml_file = tmp_path / "sample.kml"
    kml_file.write_text(_kml(body), encoding="utf-8")

    waypoints = kmz_loop.load_waypoints(kml_path=str(kml_file))

    assert "InFolder" in waypoints
    assert "OutFolder" not in waypoints
