"""T3「逐日轨迹装配与统计」的样例测试（day_tracks.py + route_points.py）。

只放 3 个最能说明主干行为的用例：村庄坐标校正、stats() 的纯函数计算、
load_gpx() 的字段顺序。完整覆盖见 tests/hidden/daytracks_test.py。
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import day_tracks  # noqa: E402
import route_points  # noqa: E402


def _write_gpx(tmp_path, points):
    """写一个最小 GPX 文件，points = [(lat, lon, ele), ...]。"""
    trkpts = "\n".join(
        f'      <trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele></trkpt>'
        for lat, lon, ele in points
    )
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" creator="test" '
        'xmlns="http://www.topografix.com/GPX/1/1">\n'
        f"  <trk><trkseg>\n{trkpts}\n  </trkseg></trk>\n"
        "</gpx>\n"
    )
    path = tmp_path / "sample.gpx"
    path.write_text(content, encoding="utf-8")
    return path


def test_daytracks_trek_villages_namche_matches_kmz_waypoint():
    """Namche 的 (lat, lon) 校正为 KMZ 标注点坐标 (27.8054, 86.7124)，
    文献海拔 3440 保持不变（不是 KMZ 记录值 3495）。
    """
    villages = {name: (lat, lon, ele) for name, lat, lon, ele in route_points.TREK_VILLAGES}
    lat, lon, ele = villages["Namche"]
    assert lat == pytest.approx(27.8054, abs=1e-4)
    assert lon == pytest.approx(86.7124, abs=1e-4)
    assert ele == 3440


def test_daytracks_stats_monotonic_ascent_day():
    """单调上升的一天：ascent 等于净高差、descent 为 0，start/end 取首末海拔。"""
    pts = [
        (86.7315, 27.6869, 2610.0),
        (86.7300, 27.6900, 2660.0),
        (86.7280, 27.6950, 2720.0),
        (86.7250, 27.7000, 2790.0),
        (86.7200, 27.7100, 2860.0),
    ]
    rows = day_tracks.stats({1: pts})
    assert len(rows) == 1
    row = rows[0]
    assert row["day"] == 1
    assert row["ascent_m"] == 250
    assert row["descent_m"] == 0
    assert row["start_ele_m"] == 2610
    assert row["end_ele_m"] == 2860


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
