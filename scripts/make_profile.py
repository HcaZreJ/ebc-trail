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

from route_points import TREK_VILLAGES as VILLAGES


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

    make_daily_profiles(plt, cum, ele_smooth, snapped)


DAILY_PNG_OUT = ROOT / "assets" / "elevation-profile-daily.png"
SEGMENTS_CSV = ROOT / "data" / "route-segments.csv"

# Everest View Hotel、Nangkartshang、Kala Patthar 不在主 GPX 轨迹上，
# 这三段和所有触及 Dingboche/Pheriche 的路段用文献海拔点连线（虚线），
# 其余在主轨迹上的路段用 GPX 逐点曲线（实线）。
EVEREST_VIEW_HOTEL_ELE = 3880
NANGKARTSHANG_ELE = 5080
PANGBOCHE_DINGBOCHE_EXT_KM = 5.3  # 10.7 减去 Tengboche–Pangboche 的 GPX 距离 5.4


def make_daily_profiles(plt, cum, ele_smooth, snapped):
    """读 data/route-segments.csv 的路段顺序与标签，逐段画海拔剖面小图，
    所有子图共享同一 x/y 轴比例尺，方便直接比较每段的强度。
    """
    # V[name] = (轨迹索引, 沿轨迹里程km, GPX海拔, 文献海拔)；
    # 实线段用 GPX 海拔（贴合真实曲线），虚线段（无 GPX 覆盖）统一用文献海拔，与表格数字一致
    V = {name: (j, cum[j] / 1000, ele_smooth[j], lit) for name, j, km, ele, lit, off in snapped}

    def gpx_curve(name_a, name_b):
        ja = V[name_a][0]
        jb = V[name_b][0]
        lo, hi = min(ja, jb), max(ja, jb)
        pts = [(cum[i] / 1000, ele_smooth[i]) for i in range(lo, hi + 1)]
        if ja > jb:
            pts = pts[::-1]
        base = pts[0][0]
        return [(abs(k - base), e) for k, e in pts]

    def reverse_curve(curve):
        length = curve[-1][0]
        return [(length - k, e) for k, e in reversed(curve)]

    def shifted(curve, offset_km):
        return [(k + offset_km, e) for k, e in curve]

    def seg_lobuche_ebc_loop():
        c1 = gpx_curve("Lobuche", "Gorak Shep")
        o1 = c1[-1][0]
        c2 = gpx_curve("Gorak Shep", "EBC")
        c2_abs = shifted(c2, o1)
        o2 = c2_abs[-1][0]
        c3_abs = shifted(reverse_curve(c2), o2)
        return [("solid", c1), ("solid", c2_abs), ("solid", c3_abs)]

    def seg_tengboche_dingboche():
        c = gpx_curve("Tengboche", "Pangboche")
        end_km, end_ele = c[-1]
        ext = [(end_km, end_ele), (end_km + PANGBOCHE_DINGBOCHE_EXT_KM, V["Dingboche"][3])]
        return [("solid", c), ("dashed", ext)]

    # order 对应 data/route-segments.csv 的 order 列，取该文件的 from/to 做小图标题
    PIECES_BY_ORDER = {
        1: lambda: [("solid", gpx_curve("Lukla", "Phakding"))],
        2: lambda: [("solid", gpx_curve("Phakding", "Namche"))],
        3: lambda: [("dashed", [(0, V["Namche"][3]), (2.5, EVEREST_VIEW_HOTEL_ELE), (5.0, V["Namche"][3])])],
        4: lambda: [("solid", gpx_curve("Namche", "Tengboche"))],
        5: seg_tengboche_dingboche,
        6: lambda: [("dashed", [(0, V["Dingboche"][3]), (3.0, NANGKARTSHANG_ELE), (6.0, V["Dingboche"][3])])],
        7: lambda: [("dashed", [(0, V["Dingboche"][3]), (9.7, V["Lobuche"][3])])],
        8: seg_lobuche_ebc_loop,
        9: lambda: [("dashed", [(0, V["Gorak Shep"][3]), (4, 5545), (8, V["Gorak Shep"][3]), (17, V["Pheriche"][3])])],
        10: lambda: [("dashed", [(0, V["Pheriche"][3]), (17, V["Namche"][3])])],
        11: lambda: [("solid", gpx_curve("Namche", "Lukla"))],
    }

    # 小图标题用短标签（完整地点说明见 route-segments.csv 对应表格）
    SHORT_TITLES = {
        1: "Lukla → Phakding",
        2: "Phakding → Namche",
        3: "Namche 往返 Everest View Hotel",
        4: "Namche → Tengboche",
        5: "Tengboche → Dingboche",
        6: "Dingboche 往返 Nangkartshang",
        7: "Dingboche → Lobuche",
        8: "Lobuche → EBC 往返",
        9: "Gorak Shep → Pheriche",
        10: "Pheriche → Namche",
        11: "Namche → Lukla",
    }

    with open(SEGMENTS_CSV, newline="") as f:
        seg_rows = list(csv.DictReader(f))

    labels, all_pieces = [], []
    for row in seg_rows:
        order = int(row["order"])
        labels.append(f"{order}. {SHORT_TITLES[order]}")
        all_pieces.append(PIECES_BY_ORDER[order]())

    x_max = max(p[0] for pieces in all_pieces for _, pts in pieces for p in pts)
    y_min, y_max = 2300, 5900

    fig, axes = plt.subplots(4, 3, figsize=(13, 15), dpi=200)
    axes_flat = axes.flatten()
    for ax, label, pieces in zip(axes_flat, labels, all_pieces):
        for style, pts in pieces:
            xs_ = [p[0] for p in pts]
            ys_ = [p[1] for p in pts]
            ax.plot(xs_, ys_, color="#2a78d6", linewidth=2,
                    linestyle="-" if style == "solid" else "--")
            ax.fill_between(xs_, ys_, y_min, color="#2a78d6", alpha=0.12, linewidth=0)
        ax.set_xlim(0, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_title(label, fontsize=10, color="#1f1f1e")
        ax.tick_params(labelsize=7.5, colors="#5f5e56")
        ax.grid(axis="y", color="#e4e3db", linewidth=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#c3c2b7")
    for ax in axes_flat[len(labels):]:
        ax.axis("off")

    fig.suptitle("12 天行程逐段海拔剖面（各段共用同一距离/海拔比例尺，方便比较强度）",
                 fontsize=13, color="#1f1f1e", y=0.995)
    fig.text(0.5, 0.005,
             "实线＝GPX 实测；虚线＝无 GPX 覆盖路段，按文献海拔点连线示意（Everest View Hotel、"
             "Nangkartshang、Kala Patthar 及 Dingboche/Pheriche 相关路段）",
             ha="center", fontsize=8.5, color="#8a897f")
    fig.tight_layout(rect=(0, 0.012, 1, 0.985))
    fig.savefig(DAILY_PNG_OUT, facecolor="white")
    print(f"wrote {DAILY_PNG_OUT}")


if __name__ == "__main__":
    main()
