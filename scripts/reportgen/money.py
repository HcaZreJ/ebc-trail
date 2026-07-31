"""美元转人民币与金额格式化。"""
from .config import RATE


def amt(v):
    return f"{int(v):,}"


def y(u):
    return f"¥{round(u * RATE):,}"


def diff(his, ours):
    return f"+{y(his - ours)}（+{round((his / ours - 1) * 100)}%）"
