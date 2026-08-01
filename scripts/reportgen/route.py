"""Section 5 路线：合并的 12 天行程表。"""
from .csvio import esc, read_csv, signed
from .imgio import img_uri
from .money import amt

HEAD = ["天", "日期", "起点", "终点", "距离", "总爬升/总下降", "终点海拔", "海拔剖面"]


def _date_disp(date_val):
    return "-".join(date_val.split("-")[1:])


def _gain_loss_cell(ascent_m, descent_m):
    up = signed(ascent_m)
    down = int(descent_m)
    down_disp = f"−{down:,}" if down > 0 else "0"
    return f"{up} / {down_disp} m"


def itinerary_table():
    it_rows = read_csv("itinerary.csv")
    it_head, it_body = it_rows[0], it_rows[1:]
    it_col = {name: i for i, name in enumerate(it_head)}

    stats_rows = read_csv("day-track-stats.csv")
    stats_head, stats_body = stats_rows[0], stats_rows[1:]
    stats_col = {name: i for i, name in enumerate(stats_head)}
    stats_by_day = {r[stats_col["day"]]: r for r in stats_body}

    out = ['<div class="table-scroll">\n<table>\n']
    out.append("<tr>" + "".join(f"<th>{esc(c)}</th>" for c in HEAD) + "</tr>\n")
    for r in it_body:
        day = r[it_col["day"]]
        # 「终点海拔」取 sleep_ele_m —— 每一行都是当天结束时所在地的海拔。
        # end_ele_m 记的是当天到达的最高点（Day 8 是往返的 EBC 5,364m，
        # 而当天终点 Gorak Shep 是 5,164m），与「终点」这一列对不上。
        end_ele = f"{amt(r[it_col['sleep_ele_m']])} m"

        if day in ("1", "12"):
            dist, gain_loss, prof_html = "—", "—", "—"
        else:
            sr = stats_by_day.get(day)
            if sr is None:
                raise SystemExit(f"day-track-stats.csv 缺 Day {day} 的数据")
            dist = f"{float(sr[stats_col['distance_km']]):.1f} km"
            gain_loss = _gain_loss_cell(sr[stats_col["ascent_m"]], sr[stats_col["descent_m"]])
            src = img_uri(f"day-profile-{int(day):02d}.png")
            prof_html = f'<img class="dayprof" src="{src}">'

        cells = [
            f"D{day}", _date_disp(r[it_col["date"]]),
            r[it_col["start_point"]], r[it_col["end_point"]],
            dist, gain_loss, end_ele,
        ]
        row_html = "".join(f"<td>{esc(c)}</td>" for c in cells)
        out.append(f"<tr>{row_html}<td>{prof_html}</td></tr>\n")
    out.append("</table>\n</div>\n")
    return "".join(out)


def tokens():
    return {"TBL_ITINERARY": itinerary_table()}
