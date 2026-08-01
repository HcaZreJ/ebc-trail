"""按天配色：地形图与海拔剖面图共用这一份，同一天在两张图里是同一个颜色。

配色按语义分三族，而不是给 11 天各配一个孤立的颜色：

- 上山日用暖色渐进（琥珀→橙→红→深绛），颜色本身读出「一天天往上走」
- 海拔适应日用紫色，它们不推进行程、只上去再下来，是另一类日子
- 下撤日用青色族，读出「往回走」

上山日与下撤日走同一条走廊，在地图上把两族分别向两侧平移，两条都看得见。

选色约束来自 OpenTopoMap 底图：底图用蓝画河流冰川、用黄绿到橙红棕的色带画海拔，
所以详图先把底图压成低饱和浅色（见 scripts/make_map.py 的 TREK_BASEMAP_MUTE），
腾出色相空间给这 11 个颜色。
"""

ASCENT_DAYS = (1, 2, 4, 5, 7, 8)
ACCLIMATIZE_DAYS = (3, 6)
DESCENT_DAYS = (9, 10, 11)

DAY_COLORS = {
    1: (242, 169, 59),    # 琥珀
    2: (232, 128, 44),
    4: (220, 90, 34),
    5: (201, 59, 34),
    7: (176, 31, 38),
    8: (140, 18, 48),     # 深绛
    3: (142, 91, 200),    # 紫：海拔适应日
    6: (107, 63, 168),
    9: (23, 162, 162),    # 青：下撤日
    10: (15, 122, 133),
    11: (11, 85, 102),
}

# 「可走的线路」底层：大环线全部导航线画成近黑，退到计划路线之后，
# 同时与浅色底图和其余灰阶元素拉开对比
OPTION_LINE = (31, 31, 30)


def hex_color(day):
    """matplotlib 用的 #rrggbb 字符串。"""
    r, g, b = DAY_COLORS[day]
    return f"#{r:02x}{g:02x}{b:02x}"


def family(day):
    """该天属于哪一族：'ascent' / 'acclimatize' / 'descent'。"""
    if day in ACCLIMATIZE_DAYS:
        return "acclimatize"
    if day in DESCENT_DAYS:
        return "descent"
    return "ascent"
