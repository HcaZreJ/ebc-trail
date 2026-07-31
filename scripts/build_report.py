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


def img_uri(name):
    p = ROOT / "assets" / name
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def esc(s):
    return html.escape(s, quote=False)


def read_csv(name):
    with open(ROOT / "data" / name, newline="") as f:
        return [row for row in csv.reader(f)]


def table(rows, header=True, total_marker=None):
    out = io.StringIO()
    out.write('<div class="table-scroll">\n<table>\n')
    for i, row in enumerate(rows):
        tag = "th" if (header and i == 0) else "td"
        cls = ' class="total"' if total_marker and row and row[0] == total_marker else ""
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

    def amt(v):
        return f"{int(v):,}"

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


def signed(v):
    n = int(v)
    return f"+{n:,}" if n > 0 else f"{n:,}" if n < 0 else "0"


def route_segments_table():
    rows = read_csv("route-segments.csv")
    head, body = rows[0], rows[1:]
    col = {name: i for i, name in enumerate(head)}
    out = [["#", "起点", "终点", "距离 km", "起点海拔 m", "终点海拔 m",
            "海拔差 m", "总爬升 m", "总下降 m"]]
    for r in body:
        out.append([
            r[col["order"]], r[col["from"]], r[col["to"]], r[col["distance_km"]],
            f"{int(r[col['start_ele_m']]):,}", f"{int(r[col['end_ele_m']]):,}",
            signed(r[col["ele_diff_m"]]),
            f"{int(r[col['ascent_m']]):,}", f"{int(r[col['descent_m']]):,}",
        ])
    return table(out)


def itinerary_dates_table():
    rows = read_csv("itinerary.csv")
    head, body = rows[0], rows[1:]
    col = {name: i for i, name in enumerate(head)}
    out = [["天", "日期", "类型", "起点", "终点"]]
    for r in body:
        out.append([r[col["day"]], r[col["date"]], r[col["day_type"]],
                    r[col["start_point"]], r[col["end_point"]]])
    return table(out)


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
    tbl_main, tbl_ref, total_cny, total_usd = cost_tables()

    reps = {
        "{{BUILD_DATE}}": date.today().isoformat(),
        "{{IMG_OVERVIEW_MAP}}": img_uri("route-map-overview.png"),
        "{{IMG_TREK_MAP}}": img_uri("route-map-trek.png"),
        "{{IMG_ELEV_PROFILE}}": img_uri("elevation-profile.png"),
        "{{IMG_ELEV_PROFILE_DAILY}}": img_uri("elevation-profile-daily.png"),
        "{{TBL_COSTS_MAIN}}": tbl_main,
        "{{TBL_COSTS_REF}}": tbl_ref,
        "{{TOTAL_CNY_RANGE}}": total_cny,
        "{{TOTAL_USD_RANGE}}": total_usd,
        "{{TBL_ROUTE_SEGMENTS}}": route_segments_table(),
        "{{TBL_ITINERARY_DATES}}": itinerary_dates_table(),
        "{{TBL_ITINERARY_FULL}}": table(read_csv("itinerary.csv")),
        "{{TBL_COSTS_FULL}}": table(read_csv("cost-breakdown.csv")),
        "{{TBL_PACKING_FULL}}": table(read_csv("packing-list.csv")),
        "{{TBL_TRACKSTATS_FULL}}": "\n".join(table(b) for b in blocks(read_csv("route-track-stats.csv"))),
        "{{TBL_ROUTE_SEGMENTS_FULL}}": table(read_csv("route-segments.csv")),
        "{{APPENDIX_SOURCES}}": sources_appendix(),
    }
    for k, v in reps.items():
        tpl = tpl.replace(k, v)

    leftovers = [t for t in ("{{",) if t in tpl]
    if leftovers:
        raise SystemExit(f"unresolved template tokens remain: {tpl[tpl.find('{{'):tpl.find('{{')+40]!r}")
    OUT.write_text(tpl)
    print(f"wrote {OUT}  ({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
