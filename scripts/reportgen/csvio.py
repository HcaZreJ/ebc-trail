"""读 data/*.csv 与文本转义。"""
import csv
import html
import re

from .config import DATA_DIR

# CSV 出处列的两种写法：`sources/07`（后面可跟裸编号 `08 14 16`）与 `sources/09-packing-gear-rental.md`。
_CITE_TOK = re.compile(r"(?:sources/)?(\d{2})(?:-[^\s]*)?$")


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


def cite(cell):
    """CSV 出处列的值 → citation 标记，抽不出编号时原样返回。

    `sources/07 08 14 16` 与 `sources/09-packing-gear-rental.md` 都抽成 `[[07,08,14,16]]`；
    标记由装配最后一步展开成上标角标，因此这里输出的是纯文本、经得起表格转义。
    """
    nums = []
    for tok in cell.split():
        m = _CITE_TOK.match(tok)
        if m and m.group(1) not in nums:
            nums.append(m.group(1))
    return "[[" + ",".join(nums) + "]]" if nums else cell


def signed(v):
    n = int(v)
    return f"+{n:,}" if n > 0 else f"{n:,}" if n < 0 else "0"
