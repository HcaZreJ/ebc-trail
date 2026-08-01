"""瓦片抓取与绘图原语，两张路线地图共用。

瓦片源 OpenTopoMap（选型依据 sources/13-map-apis.md），抓取走
http_fetch.get_bytes。缓存命中时不发请求。
"""
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

from http_fetch import get_bytes

ROOT = Path(__file__).resolve().parent.parent
TILE_URL = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
UA = "ebc-trail-report/1.0 (one-off personal trip map; contact aibrary@ouraca.ai)"
CACHE = ROOT / "assets" / ".tile-cache"

WHITE = (255, 255, 255)
GRAY = (90, 90, 86)
INK = (31, 31, 30)


def global_px(lon, lat, z):
    n = 256 * (2 ** z)
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def fetch_tile(z, x, y, i):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{z}_{x}_{y}.png"
    if not f.exists():
        url = TILE_URL.format(s="abc"[i % 3], z=z, x=x, y=y)
        data = get_bytes(url, UA, timeout=30, retries=8)
        if data[:4] != b"\x89PNG":
            raise RuntimeError(f"tile fetch returned non-PNG payload: {url}")
        f.write_bytes(data)
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
    """把底图压成低饱和浅色背景，给叠加的路线腾出色相空间。"""
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
    draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=WHITE, width=3)


def label(draw, xy, text, font, anchor="la", fill=INK):
    x, y = xy
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            draw.text((x + dx, y + dy), text, font=font, anchor=anchor, fill=WHITE)
    draw.text((x, y), text, font=font, anchor=anchor, fill=fill)


def attribution(img, font):
    draw = ImageDraw.Draw(img)
    text = "© OpenStreetMap contributors, SRTM | map style © OpenTopoMap (CC-BY-SA)"
    w = draw.textlength(text, font=font)
    draw.rectangle([img.width - w - 14, img.height - 24, img.width, img.height], fill=WHITE)
    draw.text((img.width - 7, img.height - 12), text, font=font, anchor="rm", fill=GRAY)


def offset_polyline(px_pts, dx):
    """沿每个顶点的绝对法线方向把像素折线平移 dx 像素。

    法线做符号归一化，恒指向东（`nx >= 0`；轨迹接近正东西走向、`nx`
    趋近于 0 时改为恒指向南，即 `ny >= 0`），与该点所在路径的行进方向
    无关——同一条走廊无论正着走还是反着走，传同一个 dx 都平移到同一侧，
    正值往东（或南）挪，负值往西（或北）挪。

    顶点法线取相邻两段法线之和再归一化，端点取唯一相邻段的法线，
    用来让重合的走廊（如上山与下撤同路）平移后仍是一条平顺的线。
    """
    n = len(px_pts)
    if n < 2:
        return list(px_pts)

    def _absolute(nx, ny):
        if abs(nx) < 1e-6:
            return (nx, ny) if ny >= 0 else (-nx, -ny)
        return (nx, ny) if nx >= 0 else (-nx, -ny)

    seg_normals = []
    for i in range(n - 1):
        (x0, y0), (x1, y1) = px_pts[i], px_pts[i + 1]
        dxx, dyy = x1 - x0, y1 - y0
        length = math.hypot(dxx, dyy)
        raw = (-dyy / length, dxx / length) if length else (0.0, 0.0)
        seg_normals.append(_absolute(*raw) if length else raw)
    out = []
    for i, (x, y) in enumerate(px_pts):
        if i == 0:
            nx, ny = seg_normals[0]
        elif i == n - 1:
            nx, ny = seg_normals[-1]
        else:
            nx, ny = seg_normals[i - 1][0] + seg_normals[i][0], seg_normals[i - 1][1] + seg_normals[i][1]
            norm = math.hypot(nx, ny)
            if norm:
                nx, ny = nx / norm, ny / norm
            else:
                nx, ny = seg_normals[i - 1]
        out.append((x + nx * dx, y + ny * dx))
    return out
