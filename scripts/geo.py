"""轨迹几何：距离、重采样、海拔平滑、爬升/下降、按端点切片。

三个图件脚本（day_tracks.py / make_profile.py / make_map.py）共用这一份实现。
点的统一表示是 (lon, lat, ele) 三元组，与 KML coordinates 的字段顺序一致。
"""

import math

EARTH_RADIUS_M = 6371000.0


def haversine_m(lat1, lon1, lat2, lon2):
    """两点间大圆距离（米）。"""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def cum_km(pts):
    """沿 pts 的累计里程（公里），返回列表与 pts 等长、首元素为 0.0。"""
    if not pts:
        return []
    cum = [0.0]
    for i in range(1, len(pts)):
        lon1, lat1, _ = pts[i - 1]
        lon2, lat2, _ = pts[i]
        cum.append(cum[-1] + haversine_m(lat1, lon1, lat2, lon2) / 1000.0)
    return cum


def resample(pts, step_m=25.0):
    """沿轨迹按 step_m 均匀重采样，海拔一起线性插值。首末点必定保留。"""
    if step_m <= 0:
        raise ValueError("step_m must be positive")
    if len(pts) < 2:
        return list(pts)

    cum = [0.0]
    for i in range(1, len(pts)):
        lon1, lat1, _ = pts[i - 1]
        lon2, lat2, _ = pts[i]
        cum.append(cum[-1] + haversine_m(lat1, lon1, lat2, lon2))
    total = cum[-1]

    targets = []
    d = 0.0
    while d < total:
        targets.append(d)
        d += step_m
    targets.append(total)

    n = len(pts)
    seg = 0
    result = []
    for d in targets:
        while seg < n - 2 and cum[seg + 1] < d:
            seg += 1
        seg_len = cum[seg + 1] - cum[seg]
        t = 0.0 if seg_len <= 0 else (d - cum[seg]) / seg_len
        t = max(0.0, min(1.0, t))
        lon1, lat1, ele1 = pts[seg]
        lon2, lat2, ele2 = pts[seg + 1]
        result.append((
            lon1 + (lon2 - lon1) * t,
            lat1 + (lat2 - lat1) * t,
            ele1 + (ele2 - ele1) * t,
        ))
    return result


def smooth_ele(eles, window=9):
    """滚动中位数平滑海拔序列，压掉 GPS 单点跳变。窗口在两端收缩。"""
    radius = window // 2
    n = len(eles)
    out = []
    for i in range(n):
        lo = max(0, i - radius)
        hi = min(n, i + radius + 1)
        w = sorted(eles[lo:hi])
        m = len(w)
        if m % 2 == 1:
            out.append(w[m // 2])
        else:
            out.append((w[m // 2 - 1] + w[m // 2]) / 2)
    return out


def gain_loss(eles, hyst=8.0):
    """极值追踪型滞回滤波统计 (总爬升 m, 总下降 m)。

    上行时追踪极大值，回落超过 hyst 才把这一段上行结算进 up，下行对称。
    走完序列后未结算的那段移动，幅度超过 hyst 才结算。
    单调上升返回 (末-首, 0)，不做量化截断。
    """
    if len(eles) < 2:
        return (0.0, 0.0)

    anchor = eles[0]
    extreme = eles[0]
    direction = None
    up = 0.0
    down = 0.0

    for e in eles[1:]:
        if direction is None:
            if e > extreme:
                direction = "up"
                extreme = e
            elif e < extreme:
                direction = "down"
                extreme = e
        elif direction == "up":
            if e > extreme:
                extreme = e
            elif extreme - e > hyst:
                up += extreme - anchor
                anchor = extreme
                direction = "down"
                extreme = e
        else:  # direction == "down"
            if e < extreme:
                extreme = e
            elif e - extreme > hyst:
                down += anchor - extreme
                anchor = extreme
                direction = "up"
                extreme = e

    if direction == "up":
        amount = extreme - anchor
        if amount > hyst:
            up += amount
    elif direction == "down":
        amount = anchor - extreme
        if amount > hyst:
            down += amount

    return (up, down)


def nearest_index(pts, lat, lon):
    """距 (lat, lon) 最近的点的 (索引, 距离米)。"""
    best_i = 0
    best_d = haversine_m(lat, lon, pts[0][1], pts[0][0])
    for i in range(1, len(pts)):
        d = haversine_m(lat, lon, pts[i][1], pts[i][0])
        if d < best_d:
            best_d = d
            best_i = i
    return best_i, best_d


def slice_between(pts, a, b):
    """截取 pts 上从最接近 a 到最接近 b 的子序列，方向总是从 a 走向 b。"""
    i, _ = nearest_index(pts, a[0], a[1])
    j, _ = nearest_index(pts, b[0], b[1])
    if i <= j:
        return list(pts[i:j + 1])
    return list(reversed(pts[j:i + 1]))
