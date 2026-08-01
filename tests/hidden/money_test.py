"""tests/hidden/money_test.py — 货币层（USD 基准 + NPR）与数据一致性的全面契约测试。

覆盖三部分：
1. scripts/reportgen/money.py 的四个格式化函数 amt / usd / npr / diff
   （整数、浮点、数字字符串、0、千分位、负差额、除零、全角括号与 U+2014）。
2. scripts/reportgen/config.py 的换算常量 NPR_PER_USD 与 PAX。
3. data/cost-breakdown.csv 与 data/quote-comparison.csv 的结构不变量
   （表头、合计一致性、列取值域、来源非空、全表无人民币痕迹）。

一次网络请求都不发，CSV 一律走 reportgen.csvio.read_csv 读仓库里的真实数据。
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from reportgen import config, csvio, money  # noqa: E402


COST_CSV = "cost-breakdown.csv"
QUOTE_CSV = "quote-comparison.csv"

COST_HEADER = [
    "category",
    "item",
    "unit_price_quote",
    "qty",
    "shared_by_n",
    "pp_usd",
    "in_total",
    "notes",
    "source",
]

QUOTE_HEADER = [
    "block",
    "item",
    "his_scope",
    "his_pp_usd",
    "ours_pp_usd",
    "basis",
    "source",
]

EM_DASH = "—"
CNY_MARKERS = ("¥", "CNY", "人民币")


# --------------------------------------------------------------------------
# CSV 读取辅助
# --------------------------------------------------------------------------


def _raw_table(filename):
    """read_csv 的原始返回，去掉整行皆空的行。第一行是表头。"""
    table = csvio.read_csv(filename)
    return [row for row in table if any(str(cell).strip() for cell in row)]


def _header_and_dicts(filename):
    """返回 (表头 list[str], 数据行 list[dict])，单元格两端空白已剥掉。"""
    table = _raw_table(filename)
    assert table, f"{filename} 应当至少含表头一行"
    header = [str(cell).strip() for cell in table[0]]
    body = []
    for row in table[1:]:
        cells = [str(cell).strip() for cell in row]
        cells = (cells + [""] * len(header))[: len(header)]
        body.append(dict(zip(header, cells)))
    return header, body


def _as_float(text, where):
    """把单元格解析成 float，失败时给出定位信息。"""
    try:
        return float(str(text).strip())
    except (TypeError, ValueError):  # pragma: no cover - 仅在数据违约时触发
        pytest.fail(f"{where} 应当可解析为 float，实际是 {text!r}")


# --------------------------------------------------------------------------
# money.amt
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "0"),
        (7, "7"),
        (999, "999"),
        (1000, "1,000"),
        (1194, "1,194"),
        (8123, "8,123"),
        (129200, "129,200"),
        (1234567, "1,234,567"),
    ],
)
def test_money_amt_integer_thousands_separator(value, expected):
    """amt 对整数只做千分位分组，三位以下原样输出，不带任何货币符号。"""
    assert money.amt(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (0.0, "0"),
        (0.9, "0"),
        (747.93, "747"),
        (909.70, "909"),
        (1999.99, "1,999"),
        (23.22, "23"),
    ],
)
def test_money_amt_truncates_float_toward_zero(value, expected):
    """amt 的小数处理是向零截断（沿用现有行为），不是四舍五入。"""
    assert money.amt(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("0", "0"),
        ("1194", "1,194"),
        ("8123", "8,123"),
        ("747.93", "747"),
        ("129200", "129,200"),
    ],
)
def test_money_amt_accepts_numeric_string(value, expected):
    """amt 接受数字字符串，结果与传等值数字一致。"""
    assert money.amt(value) == expected


def test_money_amt_carries_no_currency_symbol():
    """amt 是纯数字格式化：输出里既没有 USD/NPR 前缀，也没有任何人民币痕迹。"""
    out = money.amt(8123)

    assert "USD" not in out
    assert "NPR" not in out
    for marker in CNY_MARKERS:
        assert marker not in out


# --------------------------------------------------------------------------
# money.usd
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "USD 0"),
        (32, "USD 32"),
        (1015, "USD 1,015"),
        (12000, "USD 12,000"),
        (1234567, "USD 1,234,567"),
    ],
)
def test_money_usd_formats_integer_amounts(value, expected):
    """usd 给整数加 `USD ` 前缀与千分位。"""
    assert money.usd(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (747.93, "USD 748"),
        (23.22, "USD 23"),
        (909.70, "USD 910"),
        (1027.49, "USD 1,027"),
        (0.4, "USD 0"),
        (2999.6, "USD 3,000"),
    ],
)
def test_money_usd_rounds_float_to_nearest_integer(value, expected):
    """usd 的小数处理是四舍五入到整数（区别于 amt 的截断）。"""
    assert money.usd(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("0", "USD 0"),
        ("1015", "USD 1,015"),
        ("747.93", "USD 748"),
    ],
)
def test_money_usd_accepts_numeric_string(value, expected):
    """usd 接受数字字符串，结果与传等值数字一致。"""
    assert money.usd(value) == expected


@pytest.mark.parametrize(
    "value,accepted",
    [
        (2.5, {"USD 2", "USD 3"}),
        (0.5, {"USD 0", "USD 1"}),
        (1015.5, {"USD 1,015", "USD 1,016"}),
    ],
)
def test_money_usd_half_boundary_stays_within_one(value, accepted):
    """恰好 .5 的边界允许 Python round 的银行家舍入：结果落在相邻两个整数之一。"""
    assert money.usd(value) in accepted


# --------------------------------------------------------------------------
# money.npr
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "NPR 0"),
        (390, "NPR 390"),
        (1100, "NPR 1,100"),
        (3000, "NPR 3,000"),
        (21000, "NPR 21,000"),
        (129200, "NPR 129,200"),
    ],
)
def test_money_npr_formats_integer_amounts(value, expected):
    """npr 给整数加 `NPR ` 前缀与千分位。"""
    assert money.npr(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (2999.6, "NPR 3,000"),
        (389.4, "NPR 389"),
        (0.2, "NPR 0"),
        ("3000", "NPR 3,000"),
        ("390", "NPR 390"),
    ],
)
def test_money_npr_rounds_and_accepts_numeric_string(value, expected):
    """npr 四舍五入到整数，并接受数字字符串。"""
    assert money.npr(value) == expected


def test_money_usd_and_npr_prefixes_are_distinct():
    """同一个数值经 usd 与 npr 得到相同数字体、不同币种前缀。"""
    assert money.usd(3000) == "USD 3,000"
    assert money.npr(3000) == "NPR 3,000"
    assert money.usd(3000) != money.npr(3000)


# --------------------------------------------------------------------------
# money.diff
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "his,ours,expected",
    [
        (1015, 747.93, "+USD 267（+36%）"),
        (1425, 909.70, "+USD 515（+57%）"),
        (12000, 8000, "+USD 4,000（+50%）"),
        (3500, 1400, "+USD 2,100（+150%）"),
    ],
)
def test_money_diff_positive_gap(his, ours, expected):
    """his 高于 ours 时金额与百分比都带 `+`，都四舍五入到整数，金额带千分位。"""
    assert money.diff(his, ours) == expected


@pytest.mark.parametrize(
    "his,ours,expected",
    [
        (1015, 1027.93, "-USD 13（-1%）"),
        (800, 1000, "-USD 200（-20%）"),
        (500, 2000, "-USD 1,500（-75%）"),
    ],
)
def test_money_diff_negative_gap(his, ours, expected):
    """his 低于 ours 时金额与百分比都带 `-`。"""
    assert money.diff(his, ours) == expected


@pytest.mark.parametrize("value", [1, 1015, 747.93, 12000])
def test_money_diff_equal_values_is_zero_and_zero_percent(value):
    """his 与 ours 相等（且 ours 非 0）时返回 `+USD 0（+0%）`。"""
    assert money.diff(value, value) == "+USD 0（+0%）"


@pytest.mark.parametrize(
    "his,ours,expected",
    [
        (100, 0, "+USD 100（—）"),
        (2500.4, 0, "+USD 2,500（—）"),
        (12000, 0.0, "+USD 12,000（—）"),
    ],
)
def test_money_diff_zero_ours_uses_em_dash_instead_of_percent(his, ours, expected):
    """ours 为 0 时百分比位写 U+2014，金额照常输出，不抛 ZeroDivisionError。"""
    assert money.diff(his, ours) == expected


def test_money_diff_zero_ours_does_not_raise():
    """除零分支被显式接住：调用本身不抛异常，且百分比位正好是 U+2014。"""
    out = money.diff(100, 0)

    assert out.endswith(f"（{EM_DASH}）")
    assert "%" not in out


def test_money_diff_uses_fullwidth_parentheses():
    """括号是全角 U+FF08 / U+FF09，不是 ASCII 圆括号。"""
    out = money.diff(1015, 747.93)

    assert "（" in out and "）" in out
    assert "(" not in out and ")" not in out
    assert out.endswith("）")


def test_money_diff_carries_no_cny_markers():
    """diff 输出只出现 USD 口径，不含任何人民币痕迹。"""
    for out in (money.diff(1015, 747.93), money.diff(1015, 1027.93), money.diff(100, 0)):
        assert out.startswith(("+USD ", "-USD "))
        for marker in CNY_MARKERS:
            assert marker not in out


# --------------------------------------------------------------------------
# config 常量
# --------------------------------------------------------------------------


def test_money_config_exposes_npr_per_usd_and_pax():
    """config 暴露 NPR_PER_USD = 129.2 与 PAX = 6。"""
    assert hasattr(config, "NPR_PER_USD"), "config 应当暴露 NPR_PER_USD"
    assert config.NPR_PER_USD == pytest.approx(129.2)

    assert hasattr(config, "PAX"), "config 应当暴露 PAX"
    assert config.PAX == 6


def test_money_config_drops_cny_rate_constant():
    """人民币汇率常量退出：config 不再暴露 RATE。"""
    assert not hasattr(config, "RATE")


# --------------------------------------------------------------------------
# data/cost-breakdown.csv 结构不变量
# --------------------------------------------------------------------------


def test_money_cost_csv_header_is_exact_nine_columns():
    """表头恰好是九列且顺序一致；人民币列 pp_cny 退出。"""
    header, _ = _header_and_dicts(COST_CSV)

    assert header == COST_HEADER
    assert "pp_cny" not in header


def test_money_cost_csv_has_exactly_one_total_row():
    """存在且只存在一行 category == 合计。"""
    _, rows = _header_and_dicts(COST_CSV)

    totals = [r for r in rows if r["category"] == "合计"]

    assert len(totals) == 1


def test_money_cost_csv_total_equals_sum_of_in_total_yes_rows():
    """合计行 pp_usd == 所有 in_total == yes 行 pp_usd 精确求和后四舍五入，容差 ±1。"""
    _, rows = _header_and_dicts(COST_CSV)

    total_row = next(r for r in rows if r["category"] == "合计")
    declared = _as_float(total_row["pp_usd"], "合计行 pp_usd")

    exact_sum = sum(
        _as_float(r["pp_usd"], f"行 {r['item']!r} 的 pp_usd")
        for r in rows
        if r["in_total"] == "yes"
    )

    assert abs(declared - round(exact_sum)) <= 1, (
        f"合计行 {declared} 与 in_total=yes 行求和 {exact_sum}（取整 {round(exact_sum)}）不一致"
    )


def test_money_cost_csv_every_pp_usd_is_nonnegative_float():
    """每个数据行的 pp_usd 可解析为非负 float。"""
    _, rows = _header_and_dicts(COST_CSV)

    assert rows, "cost-breakdown.csv 应当有数据行"
    for row in rows:
        value = _as_float(row["pp_usd"], f"行 {row['item']!r} 的 pp_usd")
        assert value >= 0, f"行 {row['item']!r} 的 pp_usd 应当非负，实际 {value}"


def test_money_cost_csv_in_total_domain_and_em_dash_placement():
    """in_total 取值只有 yes / no / U+2014，且 U+2014 只出现在合计行。"""
    _, rows = _header_and_dicts(COST_CSV)

    for row in rows:
        assert row["in_total"] in {"yes", "no", EM_DASH}, (
            f"行 {row['item']!r} 的 in_total 取值 {row['in_total']!r} 越界"
        )
        if row["in_total"] == EM_DASH:
            assert row["category"] == "合计", (
                f"in_total 为 em dash 的行应当是合计行，实际 category={row['category']!r}"
            )


def test_money_cost_csv_source_nonempty_except_total_row():
    """除合计行外每行 source 非空。"""
    _, rows = _header_and_dicts(COST_CSV)

    for row in rows:
        if row["category"] == "合计":
            continue
        assert row["source"], f"行 {row['item']!r} 的 source 列应当非空"


def test_money_cost_csv_has_no_cny_markers_anywhere():
    """全表任何单元格都不含 ¥ / CNY / 人民币。"""
    table = _raw_table(COST_CSV)

    for row_index, row in enumerate(table):
        for cell in row:
            for marker in CNY_MARKERS:
                assert marker not in str(cell), (
                    f"cost-breakdown.csv 第 {row_index + 1} 行单元格 {cell!r} 含 {marker!r}"
                )


# --------------------------------------------------------------------------
# data/quote-comparison.csv 结构不变量
# --------------------------------------------------------------------------


def test_money_quote_csv_header_is_exact_seven_columns():
    """表头恰好是七列且顺序一致。"""
    header, _ = _header_and_dicts(QUOTE_CSV)

    assert header == QUOTE_HEADER


def test_money_quote_csv_block_domain_is_items_and_totals():
    """block 列取值只有 items 与 totals，两块都非空。"""
    _, rows = _header_and_dicts(QUOTE_CSV)

    blocks = {row["block"] for row in rows}

    assert blocks == {"items", "totals"}


def test_money_quote_csv_package_base_equals_items_sum():
    """totals 块里以 `套餐基础价` 开头的那行，ours_pp_usd == items 块求和（±0.5）。"""
    _, rows = _header_and_dicts(QUOTE_CSV)

    base_rows = [
        r for r in rows if r["block"] == "totals" and r["item"].startswith("套餐基础价")
    ]
    assert len(base_rows) == 1, "totals 块应当恰有一行 item 以 套餐基础价 开头"

    declared = _as_float(base_rows[0]["ours_pp_usd"], "套餐基础价行 ours_pp_usd")
    items_sum = sum(
        _as_float(r["ours_pp_usd"], f"items 行 {r['item']!r} 的 ours_pp_usd")
        for r in rows
        if r["block"] == "items"
    )

    assert declared == pytest.approx(items_sum, abs=0.5), (
        f"套餐基础价 {declared} 与 items 块求和 {items_sum} 不一致"
    )


def test_money_quote_csv_items_ours_pp_usd_is_nonnegative_float():
    """items 块每行 ours_pp_usd 可解析为非负 float。"""
    _, rows = _header_and_dicts(QUOTE_CSV)

    items = [r for r in rows if r["block"] == "items"]
    assert items, "quote-comparison.csv 的 items 块应当有数据行"
    for row in items:
        value = _as_float(row["ours_pp_usd"], f"items 行 {row['item']!r} 的 ours_pp_usd")
        assert value >= 0, f"items 行 {row['item']!r} 的 ours_pp_usd 应当非负，实际 {value}"


@pytest.mark.parametrize("column", ["his_pp_usd", "ours_pp_usd"])
def test_money_quote_csv_totals_amounts_are_nonnegative_floats(column):
    """totals 块每行 his_pp_usd 与 ours_pp_usd 都可解析为非负 float。"""
    _, rows = _header_and_dicts(QUOTE_CSV)

    totals = [r for r in rows if r["block"] == "totals"]
    assert totals, "quote-comparison.csv 的 totals 块应当有数据行"
    for row in totals:
        value = _as_float(row[column], f"totals 行 {row['item']!r} 的 {column}")
        assert value >= 0, f"totals 行 {row['item']!r} 的 {column} 应当非负，实际 {value}"


def test_money_quote_csv_basis_nonempty_on_every_row():
    """每行 basis 列非空。"""
    _, rows = _header_and_dicts(QUOTE_CSV)

    for row in rows:
        assert row["basis"], f"行 {row['item']!r} 的 basis 列应当非空"


def test_money_quote_csv_has_no_cny_markers_anywhere():
    """全表任何单元格都不含 ¥ / CNY / 人民币。"""
    table = _raw_table(QUOTE_CSV)

    for row_index, row in enumerate(table):
        for cell in row:
            for marker in CNY_MARKERS:
                assert marker not in str(cell), (
                    f"quote-comparison.csv 第 {row_index + 1} 行单元格 {cell!r} 含 {marker!r}"
                )


# --------------------------------------------------------------------------
# 端到端：格式化函数与 CSV 数据接得上
# --------------------------------------------------------------------------


def test_money_cost_csv_total_renders_through_usd():
    """合计行的 pp_usd 能直接喂给 usd()，渲染成 `USD <千分位整数>`。"""
    _, rows = _header_and_dicts(COST_CSV)

    total_row = next(r for r in rows if r["category"] == "合计")
    rendered = money.usd(total_row["pp_usd"])

    assert rendered.startswith("USD ")
    for marker in CNY_MARKERS:
        assert marker not in rendered


def test_money_quote_csv_totals_render_through_diff():
    """totals 块每行的 (his_pp_usd, ours_pp_usd) 都能喂给 diff()，产出带全角括号的差额串。"""
    _, rows = _header_and_dicts(QUOTE_CSV)

    totals = [r for r in rows if r["block"] == "totals"]
    assert totals, "quote-comparison.csv 的 totals 块应当有数据行"

    for row in totals:
        his = _as_float(row["his_pp_usd"], f"totals 行 {row['item']!r} 的 his_pp_usd")
        ours = _as_float(row["ours_pp_usd"], f"totals 行 {row['item']!r} 的 ours_pp_usd")

        rendered = money.diff(his, ours)

        assert rendered.startswith(("+USD ", "-USD "))
        assert rendered.endswith("）")
