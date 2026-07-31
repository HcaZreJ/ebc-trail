"""读 data/*.csv 与文本转义。"""
import csv
import html

from .config import DATA_DIR


def read_csv(name):
    with open(DATA_DIR / name, newline="") as f:
        return [row for row in csv.reader(f)]


def blocks(rows):
    """按空行把 CSV 拆成多个表块（route-track-stats.csv 有两段）"""
    block, res = [], []
    for r in rows:
        if not any(c.strip() for c in r):
            if block:
                res.append(block)
            block = []
        else:
            block.append(r)
    if block:
        res.append(block)
    return res


def esc(s):
    return html.escape(s, quote=False)


def signed(v):
    n = int(v)
    return f"+{n:,}" if n > 0 else f"{n:,}" if n < 0 else "0"
