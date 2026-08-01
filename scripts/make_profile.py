"""读 data/day-tracks.json，渲染剖面图并重算 data/route-track-stats.csv。

产物：
- assets/day-profile-02.png .. day-profile-11.png  表格内嵌用的逐日小图
- assets/elevation-profile.png                      10 天首尾相接的全程剖面
- data/route-track-stats.csv                        Day 2→Day 8（Lukla→EBC 上山
  全程）逐村吸附的累计里程、轨迹实测海拔、文献海拔、吸附偏差

不重新解析 KML/GPX：装配的事实源是 scripts/day_tracks.py 的产物 day-tracks.json。
出处见 sources/15-kmz-loop-track.md。

Run:  uv run --with matplotlib scripts/make_profile.py
"""
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import geo
from day_colors import hex_color
from profile_thumbs import day_thumbnail
from route_points import TREK_VILLAGES, KALA_PATTHAR, ACCLIMATIZE_POINTS

ROOT = Path(__file__).resolve().parent.parent
TRACKS_JSON = ROOT / "data" / "day-tracks.json"
CSV_OUT = ROOT / "data" / "route-track-stats.csv"
PNG_OUT = ROOT / "assets" / "elevation-profile.png"

Y_RANGE = (2300, 5900)

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB",
                                   "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def full_profile(day_tracks):
    """10 天首尾相接画成一条连续曲线，每天一个颜色，交界处画竖线并标 Day N；
    村庄、Kala Patthar、海拔适应点标文献海拔；适应日往返段就地凸起。
    """
    days = sorted(day_tracks)
    offsets, curves = {}, {}
    offset = 0.0
    for day in days:
        pts = day_tracks[day]
        local_km = geo.cum_km(pts)
        offsets[day] = offset
        curves[day] = ([offset + k for k in local_km], [p[2] for p in pts])
        offset += local_km[-1]
    total_km = offset

    def nearest_global(lat, lon):
        best = None
        for day in days:
            idx, dist = geo.nearest_index(day_tracks[day], lat, lon)
            if best is None or dist < best[2]:
                best = (day, idx, dist)
        day, idx, _ = best
        return curves[day][0][idx], curves[day][1][idx]

    fig, ax = plt.subplots(figsize=(18, 6), dpi=200)
    for day in days:
        xs, ys = curves[day]
        color = hex_color(day)
        ax.fill_between(xs, ys, Y_RANGE[0], color=color, alpha=0.16, linewidth=0)
        ax.plot(xs, ys, color=color, linewidth=2)

    y_top = Y_RANGE[1] - 90
    for day in days:
        x0 = offsets[day]
        ax.axvline(x0, color="#c3c2b7", linewidth=0.8, zorder=1)
        ax.text(x0 + total_km * 0.002, y_top, f"Day {day}", fontsize=8,
                 color=hex_color(day), rotation=90, va="top", ha="left")

    landmarks = list(TREK_VILLAGES) + [ACCLIMATIZE_POINTS[0], KALA_PATTHAR]
    placed = sorted(
        (nearest_global(lat, lon) + (name, lit_ele) for name, lat, lon, lit_ele in landmarks),
        key=lambda t: t[0],
    )
    dy_cycle = [24, -32, 42, -22, 34, -44]
    for i, (x, ele, name, lit_ele) in enumerate(placed):
        ax.plot(x, ele, "o", color="#1f1f1e", markersize=6,
                 markerfacecolor="white", markeredgewidth=1.6, zorder=5)
        dy = dy_cycle[i % len(dy_cycle)]
        va = "bottom" if dy > 0 else "top"
        ax.annotate(f"{name}\n{lit_ele}m", (x, ele), textcoords="offset points",
                     xytext=(0, dy), ha="center", va=va, fontsize=7.5, color="#1f1f1e")

    ax.set_xlabel("累计里程（km，10 天首尾相接）", fontsize=11, color="#1f1f1e")
    ax.set_ylabel("海拔（m）", fontsize=11, color="#1f1f1e")
    ax.set_title("EBC 徒步海拔剖面（Day 2–11，按天分色，往返段就地凸起）",
                 fontsize=13, color="#1f1f1e", pad=14)
    ax.grid(axis="y", color="#e4e3db", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors="#5f5e56")
    ax.set_ylim(*Y_RANGE)
    ax.set_xlim(0, total_km)
    ax.margins(x=0.01)
    fig.text(0.99, 0.01,
              f"数据：KMZ 实测 + GPX 实测 + OSM 步道/SRTM30m 补测，全程 {total_km:.1f} km",
              ha="right", fontsize=7.5, color="#8a897f")
    fig.tight_layout()
    fig.savefig(PNG_OUT, facecolor="white")
    plt.close(fig)
    print(f"wrote {PNG_OUT}")


# Pheriche 不在上山走廊上：上山走 Dingboche→Dughla→Lobuche，Pheriche 只在
# Day 9–10 下撤时经过，它的里程与海拔在 data/day-track-stats.csv 的 Day 9/Day 10 行里。
OFF_ASCENT_VILLAGES = {"Pheriche"}


def _write_route_track_stats(day_tracks):
    """Day 2→Day 8 接成 Lukla→EBC 上山全程，上山走廊上的村庄各自吸附到这条轨迹上。"""
    full = []
    for day in range(2, 9):
        full.extend(day_tracks[day])
    cum = geo.cum_km(full)

    rows = []
    for name, lat, lon, lit_ele in TREK_VILLAGES:
        if name in OFF_ASCENT_VILLAGES:
            continue
        idx, off_m = geo.nearest_index(full, lat, lon)
        rows.append((name, cum[idx], round(full[idx][2]), lit_ele, round(off_m)))
    rows.sort(key=lambda r: r[1])

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["village", "cum_km_from_lukla", "ele_gpx_m", "ele_literature_m", "snap_offset_m"])
        for name, km, ele, lit_ele, off_m in rows:
            w.writerow([name, round(km, 1), ele, lit_ele, off_m])
    print(f"wrote {CSV_OUT}")


def main():
    raw = json.loads(TRACKS_JSON.read_text())
    day_tracks = {int(d): [tuple(p) for p in pts] for d, pts in raw.items()}

    x_max = math.ceil(max(geo.cum_km(pts)[-1] for pts in day_tracks.values()))
    for day in sorted(day_tracks):
        day_thumbnail(day, day_tracks[day], x_max, Y_RANGE)
    print(f"wrote {len(day_tracks)} day-profile thumbnails (x_max={x_max} km, y_range={Y_RANGE})")

    full_profile(day_tracks)
    _write_route_track_stats(day_tracks)


if __name__ == "__main__":
    main()
