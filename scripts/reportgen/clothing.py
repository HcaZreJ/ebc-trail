"""Section 1 每天穿什么：温度区间与分层搭配表。

路段与宿营海拔从 itinerary.csv 按 day join 过来，不在 clothing-by-day.csv 里
另存一份——行程一改，穿衣表跟着变。

当天最高点 high_ele_m 存在 clothing-by-day.csv 里，因为 itinerary.csv 记不了它：
那张表的 end_ele_m 在多数日子等于当天最高点，但 Day 6 适应日爬到 5,080m 却记
宿营地 4,410m，Day 9 凌晨登 Kala Patthar 5,545m 却记终点 Pheriche 4,280m。白天
穿多厚由当天最高点定，不由终点定，所以这一列单独存，并由 _check_high() 校验它
不低于 itinerary 里该天的任何一个海拔，防两张表漂移。
"""
from .csvio import cite, esc, read_csv
from .money import amt

HEAD = [
    "天", "路段", "最高 / 宿营", "白天 °C", "夜间 °C",
    "行进时上身", "裤子", "日包里加带", "出处",
]


def _check_high(day, high_m, it_row, it_col):
    known = [int(it_row[it_col[c]]) for c in ("start_ele_m", "end_ele_m", "sleep_ele_m")]
    if high_m < max(known):
        raise SystemExit(
            f"clothing-by-day.csv 的 Day {day} 最高点 {high_m}m "
            f"低于 itinerary.csv 里该天的 {max(known)}m"
        )


def _ele_cell(high_m, sleep_m):
    if high_m == sleep_m:
        return f"{amt(sleep_m)} m"
    return f"{amt(high_m)} / {amt(sleep_m)} m"


def clothing_table():
    it_rows = read_csv("itinerary.csv")
    it_col = {name: i for i, name in enumerate(it_rows[0])}
    it_by_day = {r[it_col["day"]]: r for r in it_rows[1:]}

    cl_rows = read_csv("clothing-by-day.csv")
    cl_col = {name: i for i, name in enumerate(cl_rows[0])}

    out = ['<div class="table-scroll">\n<table>\n']
    out.append("<tr>" + "".join(f"<th>{esc(c)}</th>" for c in HEAD) + "</tr>\n")
    for r in cl_rows[1:]:
        day = r[cl_col["day"]]
        it = it_by_day.get(day)
        if it is None:
            raise SystemExit(f"clothing-by-day.csv 的 Day {day} 在 itinerary.csv 里没有对应行")
        high_m = int(r[cl_col["high_ele_m"]])
        _check_high(day, high_m, it, it_col)
        sleep_m = int(it[it_col["sleep_ele_m"]])
        cells = [
            f"D{day}", f"{it[it_col['start_point']]} → {it[it_col['end_point']]}",
            _ele_cell(high_m, sleep_m),
            r[cl_col["temp_day_c"]], r[cl_col["temp_night_c"]],
            r[cl_col["upper"]], r[cl_col["lower"]], r[cl_col["daypack"]],
            cite(r[cl_col["source"]]),
        ]
        out.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in cells) + "</tr>\n")
    out.append("</table>\n</div>\n")
    return "".join(out)


def tokens():
    return {"TBL_CLOTHING": clothing_table()}
