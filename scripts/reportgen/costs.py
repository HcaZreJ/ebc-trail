"""Section 8 预估总价：cost-breakdown.csv 的计入项与参考项两张表 + 合计口径。

每行是单点最佳估算（取值规则见该行 notes 与 AGENTS.md 的费用口径）。
"""
from .csvio import read_csv
from .money import amt
from .tables import table


def cost_tables():
    rows = read_csv("cost-breakdown.csv")
    head, body = rows[0], rows[1:]
    col = {name: i for i, name in enumerate(head)}

    def pick(r, name):
        return r[col[name]]

    main = [["类别", "项目", "原报价", "每人 ¥", "备注"]]
    total_cny = total_usd = None
    for r in body:
        if pick(r, "category") == "合计":
            total_cny, total_usd = pick(r, "pp_cny"), pick(r, "pp_usd")
            main.append(["合计", pick(r, "item"), "—", amt(total_cny), pick(r, "notes")])
        elif pick(r, "in_total") == "yes":
            main.append([pick(r, "category"), pick(r, "item"), pick(r, "unit_price_quote"),
                         amt(pick(r, "pp_cny")), pick(r, "notes")])
    ref = [["项目", "每人 ¥", "说明"]]
    for r in body:
        if pick(r, "in_total") == "no":
            ref.append([pick(r, "item"), amt(pick(r, "pp_cny")), pick(r, "notes")])
    return (table(main, total_marker="合计"), table(ref),
            f"¥{int(total_cny):,}", f"USD {int(total_usd):,}")


def tokens():
    tbl_main, tbl_ref, total_cny, total_usd = cost_tables()
    return {
        "TBL_COSTS_MAIN": tbl_main,
        "TBL_COSTS_REF": tbl_ref,
        "TOTAL_CNY": total_cny,
        "TOTAL_USD": total_usd,
    }
