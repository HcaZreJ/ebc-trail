"""美元转人民币与金额区间格式化。"""
from .config import RATE


def rng(lo, hi):
    lo, hi = f"{int(lo):,}", f"{int(hi):,}"
    return lo if lo == hi else f"{lo}–{hi}"


def y(u):
    return f"¥{round(u * RATE):,}"


def diff(his, ours):
    return f"+{y(his - ours)}（+{round((his / ours - 1) * 100)}%）"
