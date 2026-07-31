"""curl 子进程封装，给瓦片抓取与 OSM/高程抓取共用。

该环境 python urllib 对这些站点 TLS 握手失败（现象与规避见 scripts/tiles.py
抓瓦片的先例），统一走 subprocess 调 curl，带指数退避重试。
"""
import subprocess
import time


def get_bytes(url, ua, timeout=30, retries=5):
    """GET url，返回响应字节。重试耗尽抛 RuntimeError。"""
    last_err = None
    for attempt in range(retries):
        if attempt > 0:
            time.sleep(2 ** attempt)
        r = subprocess.run(
            ["curl", "-sSL", "--fail", "--http1.1", "-m", str(timeout), "-A", ua, url],
            capture_output=True,
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout
        last_err = (r.stderr or b"").decode("utf-8", "replace") or f"curl exit {r.returncode}"
    raise RuntimeError(f"GET failed after {retries} attempts: {url} ({last_err})")


def post_text(url, body, timeout=60, retries=5):
    """POST body 到 url，返回响应文本。重试耗尽抛 RuntimeError。"""
    last_err = None
    for attempt in range(retries):
        if attempt > 0:
            time.sleep(2 ** attempt)
        r = subprocess.run(
            ["curl", "-sS", "--fail", "-m", str(timeout), "-X", "POST", "-d", body, url],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout
        last_err = r.stderr or f"curl exit {r.returncode}"
    raise RuntimeError(f"POST failed after {retries} attempts: {url} ({last_err})")
