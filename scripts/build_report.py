"""从 report/template.html + data/*.csv + sources/*.md + assets/*.png
生成自包含的 report/EBC-report.html（图片以 base64 内嵌，可直接分享/打印成 PDF）。

Run:  uv run --with markdown scripts/build_report.py
"""
import base64
import csv
import html
import io
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "report" / "template.html"
OUT = ROOT / "report" / "EBC-report.html"

RATE = 6.8   # 1 USD ≈ 6.8 CNY（2026-07 参考价，见 AGENTS.md）
PAX = 6      # 同行人数


def img_uri(name):
    p = ROOT / "assets" / name
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def esc(s):
    return html.escape(s, quote=False)


def read_csv(name):
    with open(ROOT / "data" / name, newline="") as f:
        return [row for row in csv.reader(f)]


def table(rows, header=True, total_marker=None):
    """total_marker：首列等于它的行加粗底色；可以是一个字符串，也可以是多个。"""
    if total_marker is None:
        marks = set()
    else:
        marks = {total_marker} if isinstance(total_marker, str) else set(total_marker)
    out = io.StringIO()
    out.write('<div class="table-scroll">\n<table>\n')
    for i, row in enumerate(rows):
        tag = "th" if (header and i == 0) else "td"
        cls = ' class="total"' if row and row[0] in marks else ""
        out.write(f"<tr{cls}>" + "".join(f"<{tag}>{esc(c)}</{tag}>" for c in row) + "</tr>\n")
    out.write("</table>\n</div>\n")
    return out.getvalue()


def blocks(rows):
    """按空行把 CSV 拆成多个表块（route-track-stats.csv 有两段）"""
    block, res = [], []
    for r in rows:
        if not any(c.strip() for c in r):
            if block:
                res.append(block)
            block = []
        else:
            block.append(r)
    if block:
        res.append(block)
    return res


def cost_tables():
    rows = read_csv("cost-breakdown.csv")
    head, body = rows[0], rows[1:]
    col = {name: i for i, name in enumerate(head)}

    def pick(r, name):
        return r[col[name]]

    def rng(lo, hi):
        lo, hi = f"{int(lo):,}", f"{int(hi):,}"
        return lo if lo == hi else f"{lo}–{hi}"

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


def quote_tables():
    """代理报价评估：把报价单的套餐内容按 data/cost-breakdown.csv 的单值定价再比对。"""
    rows = read_csv("quote-comparison.csv")
    col = {name: i for i, name in enumerate(rows[0])}
    body = [r for r in rows[1:] if any(c.strip() for c in r)]

    def pick(r, name):
        return r[col[name]]

    def usd(r, name):
        v = pick(r, name).strip()
        return float(v) if v else 0.0

    def y(u):
        return f"¥{round(u * RATE):,}"

    def diff(his, ours):
        return f"+{y(his - ours)}（+{round((his / ours - 1) * 100)}%）"

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
        "{{TBL_QUOTE_ITEMS}}": table(tbl_items, total_marker="小计"),
        "{{TBL_QUOTE_TOTALS}}": table(tbl_tot, total_marker=(SELL, ALLIN)),
        "{{QUOTE_GAP_ALLIN_PCT}}": f"{round((his_all / ours_all - 1) * 100)}%",
        "{{QUOTE_BASE_OURS}}": y(base_ours),
        "{{QUOTE_GAP_PP}}": y(gap),
        "{{QUOTE_GAP_PCT}}": f"{round((his_sell / ours_sell - 1) * 100)}%",
        "{{QUOTE_GAP_GROUP}}": y(gap * PAX),
        "{{QUOTE_HIS_SELL}}": y(his_sell),
        "{{QUOTE_OURS_SELL}}": y(ours_sell),
        "{{QUOTE_HIS_ALLIN}}": y(his_all),
        "{{QUOTE_OURS_ALLIN}}": y(ours_all),
    }


def sources_appendix():
    md = markdown.Markdown(extensions=["tables"])
    out = []
    for f in sorted((ROOT / "sources").glob("*.md")):
        out.append(f'<section class="src" id="{f.stem}">')
        out.append(f'<p class="meta">sources/{f.name}</p>')
        out.append(md.reset().convert(f.read_text()))
        out.append("</section>")
    return "\n".join(out)


def main():
    tpl = TEMPLATE.read_text()
    tbl_main, tbl_ref, total_cny, total_usd, total_mid = cost_tables()

    reps = {
        "{{BUILD_DATE}}": date.today().isoformat(),
        "{{TOTAL_CNY_MID}}": total_mid,
        "{{IMG_OVERVIEW_MAP}}": img_uri("route-map-overview.png"),
        "{{IMG_TREK_MAP}}": img_uri("route-map-trek.png"),
        "{{IMG_ELEV_PROFILE}}": img_uri("elevation-profile.png"),
        "{{TBL_COSTS_MAIN}}": tbl_main,
        "{{TBL_COSTS_REF}}": tbl_ref,
        "{{TOTAL_CNY_RANGE}}": total_cny,
        "{{TOTAL_USD_RANGE}}": total_usd,
        "{{TBL_ITINERARY_FULL}}": table(read_csv("itinerary.csv")),
        "{{TBL_COSTS_FULL}}": table(read_csv("cost-breakdown.csv")),
        "{{TBL_PACKING_FULL}}": table(read_csv("packing-list.csv")),
        "{{TBL_TRACKSTATS_FULL}}": "\n".join(table(b) for b in blocks(read_csv("route-track-stats.csv"))),
        "{{TBL_QUOTE_CMP_FULL}}": table(read_csv("quote-comparison.csv")),
        "{{APPENDIX_SOURCES}}": sources_appendix(),
    }
    reps.update(quote_tables())
    for k, v in reps.items():
        tpl = tpl.replace(k, v)

    leftovers = [t for t in ("{{",) if t in tpl]
    if leftovers:
        raise SystemExit(f"unresolved template tokens remain: {tpl[tpl.find('{{'):tpl.find('{{')+40]!r}")
    OUT.write_text(tpl)
    print(f"wrote {OUT}  ({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
