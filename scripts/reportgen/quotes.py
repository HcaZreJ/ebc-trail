"""代理报价评估：把报价单的套餐内容按 data/cost-breakdown.csv 的单值定价再比对。

比价对象是套餐本体（不含餐食），分两档口径：Lukla 会合档不含向导背夫的进山交通，
加都随行档在它之上加他们的固定翼往返。全包餐是可选加购，单独列差价、不进小计。
"""
from .config import PAX
from .csvio import cite, read_csv
from .money import diff, usd
from .tables import table

BASE = "套餐基础价"
MEALS = "全包餐"
SHARED = "两边都不含"
CREW = "加购"

KTM = "小计 · 向导背夫从加都随行进山"


def tokens():
    rows = read_csv("quote-comparison.csv")
    col = {name: i for i, name in enumerate(rows[0])}
    body = [r for r in rows[1:] if any(c.strip() for c in r)]

    def pick(r, name):
        return r[col[name]]

    def num(r, name):
        v = pick(r, name).strip()
        return float(v) if v else 0.0

    items = [r for r in body if pick(r, "block") == "items"]
    totals = [r for r in body if pick(r, "block") == "totals"]

    tbl_items = [["报价单的套餐内容", "报价单口径", "我们的单值 每人", "取值依据", "出处"]]
    for r in items:
        tbl_items.append([pick(r, "item"), pick(r, "his_scope"), usd(num(r, "ours_pp_usd")),
                          pick(r, "basis"), cite(pick(r, "source"))])
    base_ours = sum(num(r, "ours_pp_usd") for r in items)
    tbl_items.append(["小计", "—", usd(base_ours), "—", "—"])

    def block_row(prefix):
        for r in totals:
            if pick(r, "item").startswith(prefix):
                return num(r, "his_pp_usd"), num(r, "ours_pp_usd")
        raise SystemExit(f"quote-comparison.csv 的 totals 块缺少以「{prefix}」开头的行")

    base_his, _ = block_row(BASE)
    meals_his, meals_ours = block_row(MEALS)
    _, crew_ours = block_row(CREW)

    ours_ktm = base_ours + crew_ours
    gap = base_his - base_ours

    tbl_tot = [["口径", "他的报价 每人", "自己组 每人", "差额", "说明"]]
    for r in totals:
        item, his, ours = pick(r, "item"), num(r, "his_pp_usd"), num(r, "ours_pp_usd")
        # 「两边都不含」两列相等，「加购」是自己组的单边附加项，两行都不是比价，差额留空。
        one_sided = item.startswith((SHARED, CREW))
        tbl_tot.append([item, usd(his), usd(ours),
                        "—" if one_sided else diff(his, ours), pick(r, "basis")])
        if item.startswith(CREW):
            tbl_tot.append([KTM, usd(base_his), usd(ours_ktm), diff(base_his, ours_ktm),
                            "自己组一列加上向导背夫的固定翼往返，他那一列不变"])

    return {
        "TBL_QUOTE_ITEMS": table(tbl_items, total_marker="小计"),
        "TBL_QUOTE_TOTALS": table(tbl_tot, total_marker=KTM),
        "QUOTE_OURS_SELL": usd(base_ours),
        "QUOTE_GAP_PP": diff(base_his, base_ours),
        "QUOTE_GAP_GROUP": usd(gap * PAX),
        "QUOTE_OURS_SELL_KTM": usd(ours_ktm),
        "QUOTE_GAP_KTM": diff(base_his, ours_ktm),
        "QUOTE_CREW_FLIGHT": usd(crew_ours),
        "QUOTE_MEALS_GAP": diff(meals_his, meals_ours),
    }
