"""用 OpenTopoMap 瓦片合成两张带地形的静态路线图：

- assets/route-map-trek.png     徒步详图（Lukla→EBC，GPX 轨迹 + 沿线村庄）
- assets/route-map-overview.png 全局图（加德满都→Lukla→EBC，含航段示意）

瓦片源：OpenTopoMap（© OpenStreetMap contributors, SRTM | © OpenTopoMap CC-BY-SA），
选型依据见 sources/13-map-apis.md。一次性抓取几十张瓦片，请求间隔 0.15s。

Run:  uv run --with pillow scripts/make_map.py
"""
import math
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from route_points import TREK_VILLAGES, KALA_PATTHAR, KATHMANDU_TIA, RAMECHHAP_AIRPORT

ROOT = Path(__file__).resolve().parent.parent
GPX = ROOT / "assets" / "Everest_Base_Camp.gpx"
TILE_URL = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
UA = "ebc-trail-report/1.0 (one-off personal trip map; contact aibrary@ouraca.ai)"
CACHE = ROOT / "assets" / ".tile-cache"

# 语义色板：两张图共用，同一条 EBC 轨迹在详图和全局图里保持同一个颜色。
# 改这里的任何一个值，两张图同时变；只想调单张图，改下面 per-figure 的线宽与底图参数。
# 选色约束来自 OpenTopoMap 底图本身：底图用蓝画河流与冰川、用黄绿到橙红棕的色带画海拔，
# 所以叠加要素落在红到洋红到紫罗兰这一段，与底图两套颜色都拉开距离。
TRAIL = (196, 30, 30)     # EBC 徒步轨迹 + 沿线村庄 marker
HELI = (216, 27, 96)      # 直升机航段 + 进出山交通节点
FIXED = (74, 58, 167)     # 固定翼航段 + Kala Patthar 支线标记
GRAY = (90, 90, 86)
INK = (31, 31, 30)
WHITE = (255, 255, 255)

# per-figure 参数：详图承担导航（保留底图等高线与冰川细节），
# 全局图只承担"三段交通怎么接上"的示意，底图压成低饱和浅色，让路线成为唯一主体。
TREK_TRAIL_W = 9
TREK_BASEMAP_MUTE = None
OVERVIEW_TRAIL_W = 7
OVERVIEW_ROUTE_W = 7
OVERVIEW_BASEMAP_MUTE = (0.30, 0.52)   # (保留饱和度, 混白比例)

FONT_LATIN = "/System/Library/Fonts/Helvetica.ttc"
FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"


def global_px(lon, lat, z):
    n = 256 * (2 ** z)
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def fetch_tile(z, x, y, i):
    # python urllib 对该瓦片源 TLS 握手失败（环境问题），改走 curl
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{z}_{x}_{y}.png"
    if not f.exists():
        for attempt in range(8):
            url = TILE_URL.format(s="abc"[(i + attempt) % 3], z=z, x=x, y=y)
            r = subprocess.run(["curl", "-sSL", "--fail", "--http1.1", "-m", "30",
                                "-A", UA, "-o", str(f), url], capture_output=True)
            if (r.returncode == 0 and f.exists()
                    and f.read_bytes()[:4] == b"\x89PNG"):
                break
            f.unlink(missing_ok=True)
            time.sleep(2 * (attempt + 1))
        else:
            raise RuntimeError(f"tile fetch failed: {url}")
        time.sleep(0.3)
    return Image.open(f).convert("RGB")


def build_basemap(bbox, z):
    """bbox = (lon_min, lat_min, lon_max, lat_max) → (image, to_px 函数)"""
    x0, y0 = global_px(bbox[0], bbox[3], z)   # 左上
    x1, y1 = global_px(bbox[2], bbox[1], z)   # 右下
    tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
    img = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    n = 0
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            img.paste(fetch_tile(z, tx, ty, n), ((tx - tx0) * 256, (ty - ty0) * 256))
            n += 1
    print(f"  fetched {n} tiles at z{z}")
    ox, oy = tx0 * 256, ty0 * 256
    img = img.crop((int(x0 - ox), int(y0 - oy), int(x1 - ox), int(y1 - oy)))

    def to_px(lon, lat):
        gx, gy = global_px(lon, lat, z)
        return gx - x0, gy - y0
    return img, to_px


def mute(img, saturation, whiten):
    """把底图压成低饱和浅色背景。OpenTopoMap 在小比例尺下整片是高饱和的橙红棕海拔色带，
    亮度和叠加线路接近，路线读不出来；降饱和再混白，把底图退到背景层。"""
    img = ImageEnhance.Color(img).enhance(saturation)
    return Image.blend(img, Image.new("RGB", img.size, WHITE), whiten)


def draw_path(draw, pts, color, width, casing=True):
    if casing:
        draw.line(pts, fill=WHITE, width=width + 4, joint="curve")
    draw.line(pts, fill=color, width=width, joint="curve")


def draw_dashed(draw, a, b, color, width=4, dash=14, gap=10, casing=None):
    dist = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / dist, (b[1] - a[1]) / dist
    t = 0.0
    while t < dist:
        t2 = min(t + dash, dist)
        seg = [(a[0] + ux * t, a[1] + uy * t), (a[0] + ux * t2, a[1] + uy * t2)]
        if casing:
            draw.line(seg, fill=casing, width=width + 4)
        draw.line(seg, fill=color, width=width)
        t = t2 + gap


def marker(draw, xy, color, r=9):
    x, y = xy
    draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=(255, 255, 255), width=3)


def label(draw, xy, text, font, anchor="la", fill=INK):
    x, y = xy
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            draw.text((x + dx, y + dy), text, font=font, anchor=anchor, fill=(255, 255, 255))
    draw.text((x, y), text, font=font, anchor=anchor, fill=fill)


def attribution(img, font):
    draw = ImageDraw.Draw(img)
    text = "© OpenStreetMap contributors, SRTM | map style © OpenTopoMap (CC-BY-SA)"
    w = draw.textlength(text, font=font)
    draw.rectangle([img.width - w - 14, img.height - 24, img.width, img.height],
                   fill=(255, 255, 255))
    draw.text((img.width - 7, img.height - 12), text, font=font, anchor="rm", fill=GRAY)


def load_track():
    ns = {"g": "http://www.topografix.com/GPX/1/1"}
    return [(float(p.get("lon")), float(p.get("lat")))
            for p in ET.parse(GPX).getroot().iter(f"{{{ns['g']}}}trkpt")]


def make_trek_map(track):
    print("trek map:")
    bbox = (86.665, 27.655, 86.895, 28.035)
    img, to_px = build_basemap(bbox, 13)
    if TREK_BASEMAP_MUTE:
        img = mute(img, *TREK_BASEMAP_MUTE)
    draw = ImageDraw.Draw(img)
    draw_path(draw, [to_px(*p) for p in track], TRAIL, TREK_TRAIL_W)

    f = ImageFont.truetype(FONT_LATIN, 26)
    f_small = ImageFont.truetype(FONT_LATIN, 22)
    # 标签统一放在点右侧，Namche/Pheriche/Gorak Shep 放左侧避免压轨迹
    left = {"Namche", "Pheriche", "Gorak Shep"}
    for name, lat, lon, ele in TREK_VILLAGES:
        xy = to_px(lon, lat)
        marker(draw, xy, HELI if name in ("Lukla", "EBC") else TRAIL)
        anchor = "rm" if name in left else "lm"
        dx = -16 if name in left else 16
        label(draw, (xy[0] + dx, xy[1]), f"{name} {ele}m",
              f if name in ("Lukla", "EBC") else f_small, anchor=anchor)
    kp = KALA_PATTHAR
    xy = to_px(kp[2], kp[1])
    draw.polygon([(xy[0], xy[1] - 12), (xy[0] - 11, xy[1] + 8), (xy[0] + 11, xy[1] + 8)],
                 fill=FIXED, outline=WHITE, width=2)
    label(draw, (xy[0] - 16, xy[1]), f"{kp[0]} {kp[3]}m", f_small, anchor="rm")

    attribution(img, ImageFont.truetype(FONT_LATIN, 15))
    out = ROOT / "assets" / "route-map-trek.png"
    img.save(out)
    print(f"  wrote {out}  {img.size}")


def make_overview_map(track):
    print("overview map:")
    bbox = (85.15, 27.28, 87.05, 28.12)
    img, to_px = build_basemap(bbox, 10)
    img = mute(img, *OVERVIEW_BASEMAP_MUTE)
    draw = ImageDraw.Draw(img)

    ktm, rhp = KATHMANDU_TIA, RAMECHHAP_AIRPORT
    lukla = TREK_VILLAGES[0]
    ebc = TREK_VILLAGES[-1]
    p_ktm, p_rhp = to_px(ktm[2], ktm[1]), to_px(rhp[2], rhp[1])
    p_lukla = to_px(lukla[2], lukla[1])

    ROAD = (72, 72, 68)   # 公路段用中性深灰：底图压浅后，深色线比原来的白线更实
    w = OVERVIEW_ROUTE_W
    draw_path(draw, [to_px(*p) for p in track], TRAIL, OVERVIEW_TRAIL_W)
    draw_dashed(draw, p_ktm, p_lukla, HELI, width=w, casing=WHITE)                # 9.25 直升机
    draw_dashed(draw, p_lukla, p_rhp, FIXED, width=w, casing=WHITE)               # 10.6 固定翼
    draw_dashed(draw, p_rhp, p_ktm, ROAD, width=w - 1, dash=10, gap=9, casing=WHITE)  # 10.6 公路

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

    # 图例（中文），框宽按文字实测
    fc = ImageFont.truetype(FONT_CJK, 22)
    lx, ly = 24, 24
    rows = [(HELI, "9.25 直升机包机 KTM→Lukla（示意）"),
            (FIXED, "10.6 固定翼 Lukla→Manthali（示意）"),
            (ROAD, "10.6 公路拼车 Manthali→KTM（示意）"),
            (TRAIL, "EBC 徒步轨迹（GPX 实测）")]
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
    track = load_track()
    make_trek_map(track)
    make_overview_map(track)
