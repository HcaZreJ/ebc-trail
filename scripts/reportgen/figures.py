"""assets/*.png 以 base64 data URI 内嵌，产物保持自包含单文件。"""
import base64

from .config import ASSETS_DIR


def img_uri(name):
    p = ASSETS_DIR / name
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def tokens():
    return {
        "IMG_OVERVIEW_MAP": img_uri("route-map-overview.png"),
        "IMG_TREK_MAP": img_uri("route-map-trek.png"),
        "IMG_ELEV_PROFILE": img_uri("elevation-profile.png"),
        "IMG_ELEV_PROFILE_DAILY": img_uri("elevation-profile-daily.png"),
    }
