"""金额格式化：美元与卢比。"""


def _num(v):
    return v if isinstance(v, (int, float)) else float(str(v).strip())


def amt(v):
    """千分位整数，不带货币符号；小数向零截断。"""
    return f"{int(_num(v)):,}"


def usd(v):
    return f"USD {round(_num(v)):,}"


def npr(v):
    return f"NPR {round(_num(v)):,}"


def diff(his, ours):
    """代理报价高出自组成本的金额与百分比；his 小于 ours 时两者都带负号。"""
    h, o = _num(his), _num(ours)
    sign = "-" if h < o else "+"
    pct = f"{sign}{abs(round((h / o - 1) * 100)):,}%" if o else "—"
    return f"{sign}USD {abs(round(h - o)):,}（{pct}）"
