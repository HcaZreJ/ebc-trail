"""tests/visible/trackgeo_test.py

样例测试（work unit T1「几何工具与 KMZ 解析」）：只覆盖主要 happy path，
作为实现时的形状参考。完整的错误用例与边界条件见 tests/hidden/trackgeo_test.py。
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import geo  # noqa: E402
import kmz_loop  # noqa: E402

KML_PATH = ROOT / "assets" / "ebc-loop.kml"


def test_trackgeo_haversine_m_known_distance():
    """标准 haversine，地球半径 6371000 m：纬度相差 1 度（同经度）的大圆距离
    精确等于 R * 弧度差，约 111.195 km。"""
    dist = geo.haversine_m(0.0, 0.0, 1.0, 0.0)

    assert dist == pytest.approx(111194.92664455874, abs=1.0)


def test_trackgeo_cum_km_accumulates_from_zero():
    """cum_km 逐点累加 haversine 距离：长度与输入相同，首元素恒为 0.0，
    后续元素单调递增（沿同一经线走 3 个等距点）。"""
    pts = [
        (0.0, 0.0, 2000.0),
        (0.0, 0.001, 2050.0),
        (0.0, 0.002, 2100.0),
    ]

    result = geo.cum_km(pts)

    assert len(result) == 3
    assert result[0] == pytest.approx(0.0)
    assert result[1] == pytest.approx(0.111195, abs=1e-3)
    assert result[2] == pytest.approx(0.222390, abs=1e-3)


def test_trackgeo_load_lines_and_waypoints_from_real_kmz():
    """真实 assets/ebc-loop.kml：导航线文件夹恰好 20 条线、总点数 17377；
    标注点文件夹里能取到已知地名，坐标与文献口径接近。"""
    lines = kmz_loop.load_lines(kml_path=str(KML_PATH))

    assert len(lines) == 20
    assert sum(len(line) for line in lines) == 17377

    waypoints = kmz_loop.load_waypoints(kml_path=str(KML_PATH))

    assert "Lukla airport" in waypoints
    lat, lon, ele = waypoints["Namche"]
    assert lat == pytest.approx(27.8054, abs=1e-3)
    assert lon == pytest.approx(86.7124, abs=1e-3)
    assert ele == pytest.approx(3494, abs=5)
