"""Section 8 预估总价：cost-breakdown.csv 的计入项与参考项两张表 + 合计口径。

每行是单点最佳估算（取值规则见该行 notes 与 AGENTS.md 的费用口径）。
"""
import re

from .csvio import cite, read_csv
from .money import npr, usd
from .tables import table

# 「原报价」列存该项报出时的原始货币，形如 NPR 3000、NPR 390/趟、USD 32/天、免费。
# 卢比数额给它补上千分位，与正文里 NPR 3,000 这样的写法对齐。
_NPR_QUOTE = re.compile(r"^NPR (\d+)(.*)$")


def _quote(text):
    m = _NPR_QUOTE.match(text)
    return npr(m.group(1)) + m.group(2) if m else text


def cost_tables():
    rows = read_csv("cost-breakdown.csv")
    head, body = rows[0], rows[1:]
    col = {name: i for i, name in enumerate(head)}

    def pick(r, name):
        return r[col[name]]

    main = [["类别", "项目", "原报价", "每人 USD", "备注", "出处"]]
    total_usd = None
    for r in body:
        if pick(r, "category") == "合计":
            total_usd = pick(r, "pp_usd")
            main.append(["合计", pick(r, "item"), "—", usd(total_usd), pick(r, "notes"),
                         cite(pick(r, "source"))])
        elif pick(r, "in_total") == "yes":
            main.append([pick(r, "category"), pick(r, "item"), _quote(pick(r, "unit_price_quote")),
                         usd(pick(r, "pp_usd")), pick(r, "notes"), cite(pick(r, "source"))])
    ref = [["项目", "每人 USD", "说明", "出处"]]
    for r in body:
        if pick(r, "in_total") == "no":
            ref.append([pick(r, "item"), usd(pick(r, "pp_usd")), pick(r, "notes"),
                        cite(pick(r, "source"))])
    return table(main, total_marker="合计"), table(ref), usd(total_usd)


def tokens():
    tbl_main, tbl_ref, total_usd = cost_tables()
    return {
        "TBL_COSTS_MAIN": tbl_main,
        "TBL_COSTS_REF": tbl_ref,
        "TOTAL_USD": total_usd,
    }
