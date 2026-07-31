"""代理报价评估：把报价单的套餐内容按 data/cost-breakdown.csv 的单值定价再比对。"""
from .config import PAX
from .csvio import read_csv
from .money import diff, y
from .tables import table


def tokens():
    rows = read_csv("quote-comparison.csv")
    col = {name: i for i, name in enumerate(rows[0])}
    body = [r for r in rows[1:] if any(c.strip() for c in r)]

    def pick(r, name):
        return r[col[name]]

    def usd(r, name):
        v = pick(r, name).strip()
        return float(v) if v else 0.0

    items = [r for r in body if pick(r, "block") == "items"]
    totals = [r for r in body if pick(r, "block") == "totals"]
    SELL = "小计：他实际卖的部分（套餐 + 全包餐）"
    ALLIN = "合计（同一行程形态：固定翼往返、9.25 宿加德满都）"

    tbl_items = [["报价单的套餐内容", "报价单口径", "我们的单值 每人", "取值依据", "出处"]]
    for r in items:
        tbl_items.append([pick(r, "item"), pick(r, "his_scope"), y(usd(r, "ours_pp_usd")),
                          pick(r, "basis"), pick(r, "source")])
    base_ours = sum(usd(r, "ours_pp_usd") for r in items)
    tbl_items.append(["小计", "—", y(base_ours), "—", "—"])

    tbl_tot = [["口径", "他的报价 每人", "自己组 每人", "差额", "说明"]]
    his_sell = ours_sell = 0.0
    shared_his = shared_ours = 0.0
    for r in totals:
        his, ours = usd(r, "his_pp_usd"), usd(r, "ours_pp_usd")
        if pick(r, "item").startswith("两边都不含"):
            tbl_tot.append([SELL, y(his_sell), y(ours_sell), diff(his_sell, ours_sell),
                            "上面两行的合计，也就是「他到底贵多少」的答案"])
            shared_his, shared_ours = his, ours
        else:
            his_sell += his
            ours_sell += ours
        tbl_tot.append([pick(r, "item"), y(his), y(ours),
                        diff(his, ours) if his > ours else "—", pick(r, "basis")])
    his_all, ours_all = his_sell + shared_his, ours_sell + shared_ours
    tbl_tot.append([ALLIN, y(his_all), y(ours_all), diff(his_all, ours_all),
                    "两边都不含的必付项在双方完全相同，不影响判断"])

    gap = his_sell - ours_sell
    return {
        "TBL_QUOTE_ITEMS": table(tbl_items, total_marker="小计"),
        "TBL_QUOTE_TOTALS": table(tbl_tot, total_marker=(SELL, ALLIN)),
        "QUOTE_GAP_ALLIN_PCT": f"{round((his_all / ours_all - 1) * 100)}%",
        "QUOTE_GAP_PP": y(gap),
        "QUOTE_GAP_PCT": f"{round((his_sell / ours_sell - 1) * 100)}%",
        "QUOTE_GAP_GROUP": y(gap * PAX),
        "QUOTE_HIS_SELL": y(his_sell),
        "QUOTE_OURS_SELL": y(ours_sell),
        "QUOTE_HIS_ALLIN": y(his_all),
    }
