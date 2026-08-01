"""用 OpenTopoMap 瓦片合成两张带地形的静态路线图：

- assets/route-map-trek.png     徒步详图：大环线全部可走线路 + 按天分色的
                                 计划路线 + 村庄/Day N/海拔适应点标注
- assets/route-map-overview.png 全局图（加德满都→Lukla→EBC，含航段示意）

瓦片抓取与绘图原语见 scripts/tiles.py。

Run:  uv run --with pillow scripts/make_map.py
"""
import json
from pathlib import Path

from PIL import ImageDraw, ImageFont

from day_colors import ASCENT_DAYS, ACCLIMATIZE_DAYS, DESCENT_DAYS, DAY_COLORS, OPTION_LINE
from kmz_loop import load_lines
from route_points import (TREK_VILLAGES, KALA_PATTHAR, ACCLIMATIZE_POINTS, LOOP_LANDMARKS,
                           KATHMANDU_TIA, RAMECHHAP_AIRPORT)
from tiles import build_basemap, mute, draw_path, draw_dashed, marker, label, attribution, offset_polyline

ROOT = Path(__file__).resolve().parent.parent
DAY_TRACKS = ROOT / "data" / "day-tracks.json"

TRAIL = (196, 30, 30)     # 全局图：EBC 徒步轨迹 + Namche marker
HELI = (216, 27, 96)      # 直升机航段 + 进出山交通节点
FIXED = (74, 58, 167)     # 固定翼航段 + Kala Patthar 支线标记
GRAY = (66, 66, 62)
INK = (31, 31, 30)
WHITE = (255, 255, 255)

FONT_LATIN = "/System/Library/Fonts/Helvetica.ttc"
FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"

# 上山日与下撤日走同一走廊：线本身平移 ±8px（线宽 9 + 白 casing 13，
# 中心相距 16px 时两条彩色线之间留出空隙，casing 不啃掉相邻线的颜色），
# Day N 徽标再多推开一点。适应日（6）是侧向支线，线不平移，徽标仍推开
# 避免压住支线。
LINE_DX = {**{d: 8 for d in ASCENT_DAYS}, **{d: -8 for d in DESCENT_DAYS}}
BADGE_DX = {**{d: 30 for d in ASCENT_DAYS}, **{d: -30 for d in DESCENT_DAYS}, 6: 55}

# 手工排布：村庄密集处（Namche/Pheriche/Dingboche/Gorak Shep/EBC/Lobuche/Tengboche/Pangboche 一带），
# 避开同一走廊上 Day N 徽标默认落点的一侧
VILLAGE_LABEL = {
    "Namche": ("rm", -34, 0), "Pheriche": ("rm", -16, -16),
    "Dingboche": ("lm", 16, 16), "Gorak Shep": ("rm", -16, -12),
    "EBC": ("lm", 16, 10), "Lobuche": ("rm", -16, -14),
    "Tengboche": ("rm", -16, 0), "Pangboche": ("rm", -16, 0),
}
ACCLI_DAY = {"Nangkartshang": 6}
# (anchor, dx, 第一行 dy, 第二行 dy)。
ACCLI_LABEL = {"Nangkartshang": ("lm", 16, -34, -12)}


def load_tracks():
    return {int(k): v for k, v in json.loads(DAY_TRACKS.read_text()).items()}


def make_trek_map():
    print("trek map:")
    img, to_px = build_basemap((86.630, 27.615, 86.900, 28.020), 13)
    img = mute(img, 0.45, 0.30)
    draw = ImageDraw.Draw(img)

    f_small = ImageFont.truetype(FONT_LATIN, 24)
    f_badge = ImageFont.truetype(FONT_LATIN, 19)
    f_cjk = ImageFont.truetype(FONT_CJK, 24)
    f_legend = ImageFont.truetype(FONT_CJK, 24)

    for line in load_lines():                                    # 层1：可走的线路
        pts = [to_px(lon, lat) for lon, lat, _ in line]
        if len(pts) >= 2:
            draw_path(draw, pts, OPTION_LINE, 7, casing=False)

    tracks = load_tracks()
    for day in range(2, 12):                                      # 层2：计划路线
        pts = [to_px(lon, lat) for lon, lat, _ in tracks[day]]
        dx = LINE_DX.get(day, 0)
        draw_path(draw, offset_polyline(pts, dx) if dx else pts, DAY_COLORS[day], 9)

    for name, lat, lon, ele in TREK_VILLAGES:                     # 层3：村庄
        xy = to_px(lon, lat)
        marker(draw, xy, HELI if name in ("Lukla", "EBC") else INK)
        anchor, dx, dy = VILLAGE_LABEL.get(name, ("lm", 16, 0))
        label(draw, (xy[0] + dx, xy[1] + dy), f"{name} {ele:,}m", f_small, anchor=anchor)

    for day in range(2, 12):                                      # 层3：Day N 徽标
        pts_px = [to_px(lon, lat) for lon, lat, _ in tracks[day]]
        bx, by = offset_polyline(pts_px, BADGE_DX.get(day, 22))[len(pts_px) // 2]
        marker(draw, (bx, by), DAY_COLORS[day], r=21)
        draw.text((bx, by), f"D{day}", font=f_badge, anchor="mm", fill=WHITE)

    for name, lat, lon, ele in ACCLIMATIZE_POINTS:                # 层3：海拔适应点
        xy = to_px(lon, lat)
        color, r = DAY_COLORS[ACCLI_DAY[name]], 10
        anchor, dx, dy1, dy2 = ACCLI_LABEL[name]
        # 标签推开到空地后画一条细引线接回方块，读者才认得出这两行属于哪个点。
        anchor_xy = (xy[0] + dx, xy[1] + dy2)
        draw.line([anchor_xy, (xy[0], xy[1])], fill=WHITE, width=5)
        draw.line([anchor_xy, (xy[0], xy[1])], fill=color, width=2)
        draw.rectangle([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], fill=color, outline=WHITE, width=3)
        label(draw, (xy[0] + dx, xy[1] + dy1), "海拔适应点", f_cjk, anchor=anchor)
        label(draw, (xy[0] + dx, xy[1] + dy2), f"{name} {ele:,}m", f_cjk, anchor=anchor)

    kp = KALA_PATTHAR
    xy = to_px(kp[2], kp[1])
    draw.polygon([(xy[0], xy[1] - 12), (xy[0] - 11, xy[1] + 8), (xy[0] + 11, xy[1] + 8)],
                 fill=FIXED, outline=WHITE, width=2)
    label(draw, (xy[0] - 16, xy[1]), f"{kp[0]} {kp[3]:,}m", f_small, anchor="rm")

    for name, lat, lon, ele in LOOP_LANDMARKS:                    # 层3：环线支线节点
        xy = to_px(lon, lat)
        marker(draw, xy, GRAY, r=6)
        label(draw, (xy[0] + 13, xy[1]), f"{name} {ele:,}m", f_cjk, anchor="lm", fill=GRAY)

    _legend_trek(draw, f_legend)
    attribution(img, ImageFont.truetype(FONT_LATIN, 15))
    out = ROOT / "assets" / "route-map-trek.png"
    img.save(out)
    print(f"  wrote {out}  {img.size}")


def _legend_trek(draw, font):
    lx, ly = 26, 26
    rows = [(OPTION_LINE, None, "大环线可走线路（KMZ 实测，全程 183.6 km）"),
            (None, ASCENT_DAYS, "上山日 Day 2–8"),
            (None, ACCLIMATIZE_DAYS, "海拔适应日 Day 6"),
            (None, DESCENT_DAYS, "下撤日 Day 9–11"),
            ("square", None, "海拔适应点")]
    box_w = 60 + max(draw.textlength(t, font=font) for *_, t in rows)
    draw.rectangle([lx - 10, ly - 10, lx + box_w, ly + 12 + len(rows) * 30], fill=WHITE, outline=GRAY)
    for i, (color, days, text) in enumerate(rows):
        y = ly + 12 + i * 30
        if days:
            seg = 44 / len(days)
            for j, d in enumerate(days):
                draw.line([(lx + 4 + j * seg, y), (lx + 4 + (j + 1) * seg, y)], fill=DAY_COLORS[d], width=7)
        elif color == "square":
            draw.rectangle([lx + 14, y - 8, lx + 30, y + 8], fill=DAY_COLORS[6], outline=WHITE, width=2)
        else:
            draw.line([(lx + 4, y), (lx + 48, y)], fill=color, width=7)
        draw.text((lx + 60, y), text, font=font, anchor="lm", fill=INK)


def make_overview_map():
    print("overview map:")
    img, to_px = build_basemap((85.15, 27.28, 87.05, 28.12), 10)
    img = mute(img, 0.30, 0.52)
    draw = ImageDraw.Draw(img)

    tracks = load_tracks()
    track = [(lon, lat) for day in range(2, 12) for lon, lat, _ in tracks[day]]

    ktm, rhp = KATHMANDU_TIA, RAMECHHAP_AIRPORT
    lukla, ebc = TREK_VILLAGES[0], TREK_VILLAGES[-1]
    p_ktm, p_rhp, p_lukla = to_px(ktm[2], ktm[1]), to_px(rhp[2], rhp[1]), to_px(lukla[2], lukla[1])

    ROAD, w = (72, 72, 68), 7
    draw_path(draw, [to_px(lon, lat) for lon, lat in track], TRAIL, w)
    draw_dashed(draw, p_ktm, p_lukla, HELI, width=w, casing=WHITE)
    draw_dashed(draw, p_lukla, p_rhp, FIXED, width=w, casing=WHITE)
    draw_dashed(draw, p_rhp, p_ktm, ROAD, width=w - 1, dash=10, gap=9, casing=WHITE)

    f = ImageFont.truetype(FONT_LATIN, 24)
    for pt, anchor, dx, dy in ((ktm, "lm", 14, -34), (rhp, "lm", 14, 18), (lukla, "lm", 14, 14)):
        xy = to_px(pt[2], pt[1])
        marker(draw, xy, HELI)
        label(draw, (xy[0] + dx, xy[1] + dy), pt[0], f, anchor=anchor)
    xy = to_px(ebc[2], ebc[1])
    marker(draw, xy, HELI)
    label(draw, (xy[0] - 14, xy[1] - 14), "Everest Base Camp", f, anchor="rm")
    nb = TREK_VILLAGES[3]
    xy = to_px(nb[2], nb[1])
    marker(draw, xy, TRAIL, r=6)
    label(draw, (xy[0] - 12, xy[1]), "Namche", ImageFont.truetype(FONT_LATIN, 20), anchor="rm")

    fc = ImageFont.truetype(FONT_CJK, 22)
    lx, ly = 24, 24
    rows = [(HELI, "9.26 进山 KTM→Lukla（交通方式待定，示意）"),
            (FIXED, "10.6 固定翼 Lukla→Manthali（示意）"),
            (ROAD, "10.6 公路拼车 Manthali→KTM（示意）"),
            (TRAIL, "EBC 徒步轨迹（KMZ 实测）")]
    box_w = 52 + 14 + max(draw.textlength(t, font=fc) for _, t in rows)
    draw.rectangle([lx - 10, ly - 10, lx + box_w, ly + 130], fill=WHITE, outline=GRAY)
    for i, (color, text) in enumerate(rows):
        y = ly + 12 + i * 30
        draw.line([(lx + 4, y), (lx + 40, y)], fill=color, width=7)
        draw.text((lx + 52, y), text, font=fc, anchor="lm", fill=INK)

    attribution(img, ImageFont.truetype(FONT_LATIN, 15))
    out = ROOT / "assets" / "route-map-overview.png"
    img.save(out)
    print(f"  wrote {out}  {img.size}")


if __name__ == "__main__":
    make_trek_map()
    make_overview_map()
