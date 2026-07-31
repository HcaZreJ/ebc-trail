"""Parse assets/Everest_Base_Camp.gpx, snap village coordinates to the track,
write data/route-track-stats.csv, and render assets/elevation-profile.png.

Run:  uv run --with matplotlib scripts/make_profile.py
"""
import csv
import math
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GPX = ROOT / "assets" / "Everest_Base_Camp.gpx"
CSV_OUT = ROOT / "data" / "route-track-stats.csv"
PNG_OUT = ROOT / "assets" / "elevation-profile.png"

NS = {"g": "http://www.topografix.com/GPX/1/1"}

# 村庄公开坐标（用于吸附到轨迹最近点）与文献海拔（来自 sources/06：EarthTrekkers / Real World Adventures）
VILLAGES = [
    ("Lukla",       27.6869, 86.7314, 2860),
    ("Phakding",    27.7433, 86.7133, 2610),
    ("Monjo",       27.7789, 86.7186, 2835),
    ("Namche",      27.8054, 86.7140, 3440),
    ("Tengboche",   27.8361, 86.7645, 3860),
    ("Pangboche",   27.8571, 86.7940, 3930),
    ("Dingboche",   27.8925, 86.8312, 4410),
    ("Pheriche",    27.8945, 86.8190, 4280),
    ("Lobuche",     27.9490, 86.8102, 4940),
    ("Gorak Shep",  27.9812, 86.8283, 5164),
    ("EBC",         28.0026, 86.8528, 5364),
]


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def rolling_median(vals, k=21):
    half = k // 2
    out = []
    for i in range(len(vals)):
        w = sorted(vals[max(0, i - half): i + half + 1])
        out.append(w[len(w) // 2])
    return out


def main():
    pts = []
    for tp in ET.parse(GPX).getroot().iter(f"{{{NS['g']}}}trkpt"):
        pts.append((float(tp.get("lat")), float(tp.get("lon")),
                    float(tp.find("g:ele", NS).text)))
    print(f"trackpoints: {len(pts)}  start ele {pts[0][2]:.0f}m  end ele {pts[-1][2]:.0f}m")

    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + haversine_m(*pts[i - 1][:2], *pts[i][:2]))
    total_km = cum[-1] / 1000
    print(f"track length (one way): {total_km:.1f} km")

    ele_smooth = rolling_median([p[2] for p in pts])

    # 吸附村庄
    snapped = []
    for name, lat, lon, lit_ele in VILLAGES:
        j = min(range(len(pts)), key=lambda i: haversine_m(lat, lon, pts[i][0], pts[i][1]))
        off_m = haversine_m(lat, lon, pts[j][0], pts[j][1])
        snapped.append((name, j, cum[j] / 1000, ele_smooth[j], lit_ele, off_m))
        print(f"{name:11s} km {cum[j]/1000:6.1f}  ele_gpx {ele_smooth[j]:6.0f}  "
              f"ele_lit {lit_ele:5d}  d_ele {ele_smooth[j]-lit_ele:+6.0f}  snap_off {off_m:6.0f} m")

    # 相邻村庄段的距离与爬升/下降（按轨迹顺序过滤掉吸附失败的村）
    on_track = [s for s in snapped if s[5] < 400]
    on_track.sort(key=lambda s: s[1])
    rows = []
    def gain_loss(seg, hyst=15.0):
        # 滞回滤波：只有偏离当前锚点超过 hyst 米才计入，压掉 GPS 海拔噪声
        up = down = 0.0
        anchor = seg[0]
        for e in seg[1:]:
            if e - anchor >= hyst:
                up += e - anchor
                anchor = e
            elif anchor - e >= hyst:
                down += anchor - e
                anchor = e
        return up, down

    NOISY = {("Monjo", "Namche"), ("Phakding", "Monjo")}
    for a, b in zip(on_track, on_track[1:]):
        up, down = gain_loss(ele_smooth[a[1]: b[1] + 1])
        note = ("峡谷段 GPS 海拔噪声大，爬升偏高，以文献数据为准"
                if (a[0], b[0]) in NOISY else "")
        rows.append((a[0], b[0], round(b[2] - a[2], 1), round(up), round(down), note))
    with open(CSV_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["village", "cum_km_from_lukla", "ele_gpx_m", "ele_literature_m", "snap_offset_m"])
        for name, _, km, ele, lit, off in snapped:
            w.writerow([name, round(km, 1), round(ele), lit, round(off)])
        w.writerow([])
        w.writerow(["segment_from", "segment_to", "distance_km", "ascent_m", "descent_m", "note"])
        w.writerows(rows)
    print(f"wrote {CSV_OUT}")

    # 画图
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB",
                                       "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    xs = [c / 1000 for c in cum]
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=200)
    ax.fill_between(xs, ele_smooth, 2300, color="#2a78d6", alpha=0.14, linewidth=0)
    ax.plot(xs, ele_smooth, color="#2a78d6", linewidth=2)

    for name, j, km, ele, lit, off in snapped:
        if off > 400:
            # 村庄在轨迹旁（如 Dingboche/Pheriche 在谷底、轨迹走高线）：
            # 空心标记画在文献海拔处，避免把村庄海拔画错
            ax.plot(km, lit, "o", markersize=8, markerfacecolor="white",
                    markeredgecolor="#2a78d6", markeredgewidth=2, zorder=5)
            dy = 24 if lit > ele else -14
            va = "bottom" if dy > 0 else "top"
            ax.annotate(f"{name}\n{lit}m（轨迹旁）", (km, lit), textcoords="offset points",
                        xytext=(0, dy), ha="center", va=va, fontsize=9, color="#1f1f1e")
            continue
        ax.plot(km, ele, "o", color="#2a78d6", markersize=8,
                markeredgecolor="white", markeredgewidth=2, zorder=5)
        dy = 24 if name != "Pheriche" else -14
        va = "bottom" if dy > 0 else "top"
        ax.annotate(f"{name}\n{lit}m", (km, ele), textcoords="offset points",
                    xytext=(0, dy), ha="center", va=va, fontsize=9, color="#1f1f1e")

    ax.set_xlabel("距 Lukla 里程（km，单程）", fontsize=11, color="#1f1f1e")
    ax.set_ylabel("海拔（m）", fontsize=11, color="#1f1f1e")
    ax.set_title("EBC 徒步海拔剖面（Lukla → Everest Base Camp 单程，返程沿同一走廊）",
                 fontsize=13, color="#1f1f1e", pad=14)
    ax.grid(axis="y", color="#e4e3db", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors="#5f5e56")
    ax.set_ylim(2300, 5900)
    ax.margins(x=0.02)
    fig.text(0.99, 0.01,
             "数据：Real World Adventures GPX（outdooractive 240405054）；Kala Patthar 5545m 为 Gorak Shep 旁支线，不在主轨迹上",
             ha="right", fontsize=7.5, color="#8a897f")
    fig.tight_layout()
    fig.savefig(PNG_OUT, facecolor="white")
    print(f"wrote {PNG_OUT}")


if __name__ == "__main__":
    main()
