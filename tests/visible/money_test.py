"""tests/visible/money_test.py

样例测试（work unit「货币层（USD 基准 + NPR）与数据一致性」）：只覆盖主要
happy path，作为实现时的形状参考。完整的错误用例、边界条件与两张费用 CSV
的结构不变量见 tests/hidden/money_test.py。
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from reportgen import money  # noqa: E402


def test_money_amt_thousands_and_truncation():
    """amt 只做千分位整数格式化，不带货币符号；小数向零截断；接受数字字符串。"""
    assert money.amt(8123) == "8,123"
    assert money.amt("1194") == "1,194"
    assert money.amt(747.93) == "747"


def test_money_usd_and_npr_carry_currency_prefix():
    """usd / npr 四舍五入到整数并加千分位，前缀分别是 `USD ` 与 `NPR `。"""
    assert money.usd(1015) == "USD 1,015"
    assert money.usd(747.93) == "USD 748"
    assert money.usd(0) == "USD 0"

    assert money.npr(3000) == "NPR 3,000"
    assert money.npr(1100) == "NPR 1,100"
    assert money.npr(390) == "NPR 390"


def test_money_diff_positive_gap():
    """diff 给出代理报价高出自组成本的金额与百分比，都四舍五入到整数，全角括号。"""
    assert money.diff(1015, 747.93) == "+USD 267（+36%）"
    assert money.diff(1425, 909.70) == "+USD 515（+57%）"
