"""assets/*.png 以 base64 data URI 内嵌，产物保持自包含单文件。"""
from .imgio import img_uri


def tokens():
    return {
        "IMG_OVERVIEW_MAP": img_uri("route-map-overview.png"),
        "IMG_TREK_MAP": img_uri("route-map-trek.png"),
        "IMG_ELEV_PROFILE": img_uri("elevation-profile.png"),
    }
