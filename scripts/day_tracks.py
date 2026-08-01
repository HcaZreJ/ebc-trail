"""把 KMZ 导航线、GPX 轨迹与补测段装配成 10 天徒步的逐日轨迹，算里程与爬升/下降。

Day 1（加德满都，不进山）与 Day 12（转场日 Lukla → 加德满都）没有徒步轨迹，不进产物。
只在 Dingboche 安排一个适应日（见 sources/16、17）。

产物：
- data/day-tracks.json    {"1": [[lon, lat, ele], ...], ...}  给剖面图与地图用
- data/day-track-stats.csv 逐日里程与爬升/下降  给报告表格用

出处见 sources/15-kmz-loop-track.md。

Run:  uv run scripts/day_tracks.py
"""
import csv
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import geo
import kmz_loop
import route_points

ROOT = Path(__file__).resolve().parent.parent
GPX = ROOT / "assets" / "Everest_Base_Camp.gpx"
GAP_LEGS = ROOT / "data" / "gap-legs.json"
TRACKS_OUT = ROOT / "data" / "day-tracks.json"
STATS_OUT = ROOT / "data" / "day-track-stats.csv"

GPX_NS = "http://www.topografix.com/GPX/1/1"

RESAMPLE_STEP_M = 25.0
# 25 m 重采样下窗口 5 跨 100 m，远大于手机 GPS 高程噪声的相关长度（几米到二十米），
# 配合 8 m 滞回足够压掉抖动；再放大到 9（跨 200 m）就开始抹掉真实的折返地形。
# 标定依据与敏感度实测见 sources/15-kmz-loop-track.md。
SMOOTH_WINDOW = 5
HYSTERESIS_M = 8.0

# 每天的数据来源，与 assemble() 的拼接表一一对应。点序列本身推不出来源，
# stats() 从这里查表填进 day-track-stats.csv 的 source 列。
DAY_SOURCES = {
    2: "KMZ 实测",
    3: "KMZ 实测",
    4: "KMZ 实测",
    5: "KMZ 实测",
    6: "OSM+SRTM30m",
    7: "GPX 实测",
    8: "GPX 实测 + KMZ 实测",
    9: "KMZ 实测 + OSM+SRTM30m",
    10: "OSM+SRTM30m + GPX 实测",
    11: "KMZ 实测",
}


def load_gpx(gpx_path=GPX):
    """GPX 轨迹点 [(lon, lat, ele)]，按文件里的点序（Lukla → EBC）。"""
    root = ET.parse(str(Path(gpx_path))).getroot()
    tag = f"{{{GPX_NS}}}trkpt"
    ele_tag = f"{{{GPX_NS}}}ele"
    pts = []
    for trkpt in root.iter(tag):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele_el = trkpt.find(ele_tag)
        ele = float(ele_el.text) if ele_el is not None and ele_el.text else 0.0
        pts.append((lon, lat, ele))
    return pts


def load_gap_legs(path=GAP_LEGS):
    """data/gap-legs.json → {leg_id: [(lon, lat, ele)]}。

    文件结构是 {leg_id: {"points": [[lon, lat, ele], ...], "source": str}}，
    本函数只取每段的 points，丢掉 source。
    """
    data = json.loads(Path(path).read_text())
    return {leg_id: [tuple(p) for p in entry["points"]] for leg_id, entry in data.items()}


def assemble(lines, gpx, legs):
    """按下表拼出 {2..11: [(lon, lat, ele)]}，每天都 resample + smooth 过。

    lines 是 kmz_loop.load_lines() 的 20 条线（下标从 0 起），gpx 是 load_gpx() 的点序列，
    legs 是 load_gap_legs() 的补测段。切片一律走 geo.slice_between，端点坐标取
    route_points 里的村庄坐标。Day 1（加都）与 Day 12（转场）没有轨迹，不在这张表里；
    行程只在 Dingboche 安排适应日，不装配 Namche 往返段。

    D2  Lukla→Phakding             lines[5]
    D3  Phakding→Namche            lines[6]
    D4  Namche→Tengboche           lines[7] 切 Namche→Tengboche
    D5  Tengboche→Dingboche        lines[7] 切 Tengboche→Pangboche + lines[8] 切 Pangboche→Dingboche
    D6  Dingboche 往返海拔适应点     legs["dingboche-nangkartshang"]
    D7  Dingboche→Lobuche          gpx 切 Dingboche→Lobuche（经 Dughla）
    D8  Lobuche→Gorak Shep→EBC 往返 gpx 切 Lobuche→Gorak Shep + lines[12]
    D9  Gorak Shep→KP 往返→Pheriche lines[13] + legs["lobuche-pheriche"]
    D10 Pheriche→Tengboche→Namche  legs["pheriche-pangboche"] + gpx 切 Pangboche→Namche
    D11 Namche→Lukla               lines[18] 切 Namche→Lukla

    lines[12] 本身就是 Gorak Shep → EBC → 返 Gorak Shep 的完整往返（7.8 km），直接接在
    D8 的后半，不用再切。lines[13] 本身就是 Gorak Shep → Kala Patthar → 返 Gorak Shep →
    Lobuche 的完整序列（8.5 km），直接做 D9 的前半，不用再切。
    """
    villages = {name: (lat, lon) for name, lat, lon, _ in route_points.TREK_VILLAGES}

    def cut(line, a_name, b_name):
        return geo.slice_between(line, villages[a_name], villages[b_name])

    def join(*segments):
        result = list(segments[0])
        for seg in segments[1:]:
            result.extend(list(seg)[1:])
        return result

    raw = {
        2: list(lines[5]),
        3: list(lines[6]),
        4: cut(lines[7], "Namche", "Tengboche"),
        5: join(cut(lines[7], "Tengboche", "Pangboche"), cut(lines[8], "Pangboche", "Dingboche")),
        6: list(legs["dingboche-nangkartshang"]),
        7: cut(gpx, "Dingboche", "Lobuche"),
        8: join(cut(gpx, "Lobuche", "Gorak Shep"), lines[12]),
        9: join(lines[13], legs["lobuche-pheriche"]),
        10: join(legs["pheriche-pangboche"], cut(gpx, "Pangboche", "Namche")),
        11: cut(lines[18], "Namche", "Lukla"),
    }

    result = {}
    for day, pts in raw.items():
        resampled = geo.resample(pts, RESAMPLE_STEP_M)
        eles = [p[2] for p in resampled]
        smoothed = geo.smooth_ele(eles, SMOOTH_WINDOW)
        result[day] = [
            (lon, lat, se) for (lon, lat, _), se in zip(resampled, smoothed)
        ]
    return result


def _round_half_up(value, ndigits=0):
    """四舍五入取整，避免 Python round() 的银行家舍入在 .5 边界上的偏差。"""
    factor = 10 ** ndigits
    result = math.floor(value * factor + 0.5) / factor
    return result if ndigits > 0 else int(result)


def stats(day_tracks):
    """{day: pts} → [{day, distance_km, ascent_m, descent_m, start_ele_m, end_ele_m, source}]。

    输入已由 assemble() 重采样并平滑，这里不再平滑，直接在收到的点上算。
    distance_km 保留一位小数，海拔与爬升/下降取整，source 查 DAY_SOURCES。
    返回按 day 升序。
    """
    rows = []
    for day in sorted(day_tracks):
        pts = day_tracks[day]
        eles = [p[2] for p in pts]
        distance_km = geo.cum_km(pts)[-1] if pts else 0.0
        ascent, descent = geo.gain_loss(eles, HYSTERESIS_M)
        rows.append({
            "day": day, "distance_km": _round_half_up(distance_km, 1),
            "ascent_m": _round_half_up(ascent), "descent_m": _round_half_up(descent),
            "start_ele_m": _round_half_up(eles[0]) if eles else 0,
            "end_ele_m": _round_half_up(eles[-1]) if eles else 0,
            "source": DAY_SOURCES.get(day, "来源未标注")})
    return rows


def main():
    """写 data/day-tracks.json 与 data/day-track-stats.csv。"""
    lines = kmz_loop.load_lines()
    gpx = load_gpx()
    legs = load_gap_legs()
    day_tracks = assemble(lines, gpx, legs)
    rows = stats(day_tracks)

    tracks_json = {
        str(day): [[round(lon, 6), round(lat, 6), round(ele, 1)] for lon, lat, ele in day_tracks[day]]
        for day in sorted(day_tracks)
    }
    TRACKS_OUT.parent.mkdir(exist_ok=True)
    TRACKS_OUT.write_text(json.dumps(tracks_json, ensure_ascii=False, indent=2))

    with STATS_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["day", "distance_km", "ascent_m", "descent_m", "start_ele_m", "end_ele_m", "source"]
        )
        for row in rows:
            writer.writerow([
                row["day"], row["distance_km"], row["ascent_m"], row["descent_m"],
                row["start_ele_m"], row["end_ele_m"], row["source"],
            ])

    print(f"wrote {TRACKS_OUT} and {STATS_OUT}")


if __name__ == "__main__":
    main()
