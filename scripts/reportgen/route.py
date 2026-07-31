"""Section 5 路线：路段库表与日期安排表。"""
from .csvio import read_csv, signed
from .tables import table


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


def tokens():
    return {
        "TBL_ROUTE_SEGMENTS": route_segments_table(),
        "TBL_ITINERARY_DATES": itinerary_dates_table(),
    }
