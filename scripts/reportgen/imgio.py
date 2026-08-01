"""assets/*.png 以 base64 data URI 内嵌，figures.py 与 route.py 共用。"""
import base64

from .config import ASSETS_DIR


def img_uri(name):
    p = ASSETS_DIR / name
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
