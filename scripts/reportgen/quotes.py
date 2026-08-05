"""代理报价评估：把报价单的套餐内容按 data/cost-breakdown.csv 的单值定价再比对。

两档口径：Lukla 会合档不含向导背夫的进山交通，加都随行档在它之上加他们的固定翼往返。
"""
from .config import PAX
from .csvio import cite, read_csv
from .money import diff, usd
from .tables import table

BASE = "套餐基础价"
MEALS = "全包餐"
SHARED = "两边都不含"
CREW = "加购"

LUKLA = "小计 · 向导背夫在 Lukla 会合"
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

    def pct(a, b):
        """a 比 b 高出的百分比；b 为 0 时写破折号，与 money.diff 的口径一致。"""
        return f"{round((a / b - 1) * 100)}%" if b else "—"

    base_his, _ = block_row(BASE)
    meals_his, meals_ours = block_row(MEALS)
    crew_his, crew_ours = block_row(CREW)

    his_sell = base_his + meals_his
    ours_sell = base_ours + meals_ours
    his_ktm, ours_ktm = his_sell + crew_his, ours_sell + crew_ours
    gap, gap_ktm = his_sell - ours_sell, his_ktm - ours_ktm

    tbl_tot = [["口径", "他的报价 每人", "自己组 每人", "差额", "说明"]]
    for r in totals:
        item, his, ours = pick(r, "item"), num(r, "his_pp_usd"), num(r, "ours_pp_usd")
        # 「两边都不含」两列相等，「加购」是自己组的单边附加项，两行都不是比价，差额留空。
        one_sided = item.startswith((SHARED, CREW))
        tbl_tot.append([item, usd(his), usd(ours),
                        "—" if one_sided else diff(his, ours), pick(r, "basis")])
        if item.startswith(MEALS):
            tbl_tot.append([LUKLA, usd(his_sell), usd(ours_sell), diff(his_sell, ours_sell),
                            "他实际卖的部分（套餐 + 全包餐）与自己组同口径相比，也就是「他到底贵多少」的答案"])
        elif item.startswith(CREW):
            tbl_tot.append([KTM, usd(his_ktm), usd(ours_ktm), diff(his_ktm, ours_ktm),
                            "自己组一列加上向导背夫的往返机票，他那一列不变"])

    return {
        "TBL_QUOTE_ITEMS": table(tbl_items, total_marker="小计"),
        "TBL_QUOTE_TOTALS": table(tbl_tot, total_marker=(LUKLA, KTM)),
        "QUOTE_OURS_SELL": usd(ours_sell),
        "QUOTE_GAP_PP": diff(his_sell, ours_sell),
        "QUOTE_GAP_GROUP": usd(gap * PAX),
        "QUOTE_OURS_SELL_KTM": usd(ours_ktm),
        "QUOTE_GAP_KTM": diff(his_ktm, ours_ktm),
        "QUOTE_GAP_KTM_GROUP": usd(gap_ktm * PAX),
        "QUOTE_CREW_FLIGHT": usd(crew_ours),
        "QUOTE_MEALS_SHARE": pct(meals_his - meals_ours + gap, gap),
    }
