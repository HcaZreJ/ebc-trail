"""Section 8 预估总价：cost-breakdown.csv 的计入项与参考项两张表 + 合计口径。"""
from .csvio import read_csv
from .money import rng
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
            total_cny = (pick(r, "pp_low_cny"), pick(r, "pp_high_cny"))
            total_usd = (pick(r, "pp_low_usd"), pick(r, "pp_high_usd"))
            main.append(["合计", pick(r, "item"), "—", rng(*total_cny), pick(r, "notes")])
        elif pick(r, "in_total") == "yes":
            main.append([pick(r, "category"), pick(r, "item"), pick(r, "unit_price_quote"),
                         rng(pick(r, "pp_low_cny"), pick(r, "pp_high_cny")), pick(r, "notes")])
    ref = [["项目", "每人 ¥", "说明"]]
    for r in body:
        if pick(r, "in_total") == "no":
            ref.append([pick(r, "item"),
                        rng(pick(r, "pp_low_cny"), pick(r, "pp_high_cny")), pick(r, "notes")])
    mid = (int(total_cny[0]) + int(total_cny[1])) / 2
    return (table(main, total_marker="合计"), table(ref),
            f"¥{int(total_cny[0]):,}–{int(total_cny[1]):,}",
            f"USD {int(total_usd[0]):,}–{int(total_usd[1]):,}",
            f"¥{round(mid):,}")


def tokens():
    tbl_main, tbl_ref, total_cny, total_usd, total_mid = cost_tables()
    return {
        "TBL_COSTS_MAIN": tbl_main,
        "TBL_COSTS_REF": tbl_ref,
        "TOTAL_CNY_RANGE": total_cny,
        "TOTAL_USD_RANGE": total_usd,
        "TOTAL_CNY_MID": total_mid,
    }
