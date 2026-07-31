"""补测两份实测轨迹都没走的 4 段路线：OSM 步道几何 + SRTM30m 高程。

大环线 KMZ 走的是 Kongma La / Cho La，绕开了 Dughla–Pheriche 那条谷；两个适应日的
支线两份轨迹也都没走。这 4 段用 OSM 的步道几何连出走线，再逐点采 SRTM30m 高程，
结果缓存进 data/gap-legs.json，构建期不再发网络请求。

出处与 API 用法见 sources/15-kmz-loop-track.md。

Run:  uv run scripts/gap_legs.py [--refresh]
"""
import json
import math
import subprocess
import time
from pathlib import Path

from geo import haversine_m
from osm_graph import build_graph, shortest_path, nearest_node

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "gap-legs.json"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ELEVATION_URL = "https://api.opentopodata.org/v1/srtm30m"

# (leg_id, 起点(lat, lon), 终点(lat, lon), bbox(南, 西, 北, 东), 是否往返)
LEGS = [
    ("namche-everest-view", (27.8054, 86.7124), (27.8167, 86.7235),
     (27.800, 86.705, 27.828, 86.740), True),
    ("dingboche-nangkartshang", (27.8895, 86.8273), (27.9055, 86.8355),
     (27.885, 86.820, 27.912, 86.845), True),
    ("lobuche-pheriche", (27.9478, 86.8104), (27.8941, 86.8198),
     (27.888, 86.795, 27.952, 86.825), False),
    ("pheriche-pangboche", (27.8941, 86.8198), (27.8547, 86.7908),
     (27.850, 86.785, 27.898, 86.825), False),
]


def _fill_none_elevations(values):
    n = len(values)
    result = list(values)
    i = 0
    while i < n:
        if result[i] is not None:
            i += 1
            continue
        j = i
        while j < n and result[j] is None:
            j += 1
        left = result[i - 1] if i > 0 else None
        right = result[j] if j < n else None
        span = j - i + 1
        for k in range(i, j):
            if left is None and right is None:
                result[k] = 0.0
            elif left is None:
                result[k] = right
            elif right is None:
                result[k] = left
            else:
                t = (k - i + 1) / span
                result[k] = left + (right - left) * t
        i = j
    return result


def fetch_elevations(coords):
    """逐点采 SRTM30m 高程，返回与 coords 等长的海拔列表。"""
    coords = list(coords)
    elevations = [None] * len(coords)
    for batch_idx in range(0, len(coords), 100):
        if batch_idx > 0:
            time.sleep(1.1)
        batch = coords[batch_idx:batch_idx + 100]
        locations = "|".join(f"{lat:.6f},{lon:.6f}" for lat, lon in batch)
        url = f"{ELEVATION_URL}?locations={locations}"
        parsed = None
        for attempt in range(3):
            if attempt > 0:
                time.sleep(0.5)
            r = subprocess.run(["curl", "-sS", url], capture_output=True, text=True)
            if r.returncode == 0:
                try:
                    candidate = json.loads(r.stdout)
                except (json.JSONDecodeError, TypeError):
                    candidate = None
                if candidate and candidate.get("status") == "OK":
                    parsed = candidate
                    break
        if parsed is None:
            raise RuntimeError(f"elevation fetch failed for batch starting at {batch_idx}")
        for offset, item in enumerate(parsed["results"]):
            elevations[batch_idx + offset] = item.get("elevation")
    return _fill_none_elevations(elevations)


def _sample_line(start, goal, step_m):
    total = haversine_m(start[0], start[1], goal[0], goal[1])
    if total == 0:
        return [start]
    n = max(1, math.ceil(total / step_m))
    return [
        (start[0] + (goal[0] - start[0]) * i / n, start[1] + (goal[1] - start[1]) * i / n)
        for i in range(n + 1)
    ]


def _overpass_fetch(bbox):
    query = ('[out:json][timeout:60];'
              f'way["highway"~"path|footway|track|steps"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});'
              'out body geom;')
    parsed = None
    for attempt in range(5):
        if attempt > 0:
            time.sleep(5 * attempt)
        r = subprocess.run(["curl", "-sS", "-X", "POST", "-d", query, OVERPASS_URL],
                            capture_output=True, text=True)
        try:
            candidate = json.loads(r.stdout)
        except (json.JSONDecodeError, TypeError):
            candidate = None
        if isinstance(candidate, dict) and "elements" in candidate:
            parsed = candidate
            break
    if parsed is None:
        raise RuntimeError(f"overpass fetch failed for bbox {bbox}")
    return parsed


def build_leg(leg_id, start, goal, bbox, out_and_back):
    """拼出一段的 {'id', 'points': [[lon, lat, ele]], 'source'}。"""
    overpass_json = _overpass_fetch(bbox)
    nodes, adj = build_graph(overpass_json)

    start_id = nearest_node(nodes, start)
    goal_id = nearest_node(nodes, goal)

    path = None
    if start_id is not None and goal_id is not None:
        path = shortest_path(nodes, adj, start_id, goal_id)

    if path is None:
        coords = _sample_line(start, goal, 100.0)
        source = "OSM 步道不连通，按直线采样 SRTM30m"
    else:
        coords = path
        source = "OSM 步道几何 + SRTM30m"

    if out_and_back:
        coords = coords + list(reversed(coords[:-1]))

    eles = fetch_elevations(coords)
    points = [[round(lon, 6), round(lat, 6), round(ele, 1)]
              for (lat, lon), ele in zip(coords, eles)]
    return {"id": leg_id, "points": points, "source": source}


def main(refresh=False):
    """写 data/gap-legs.json；已含全部 4 段且未加 --refresh 时直接返回。

    产物结构以 leg_id 为键，坐标 6 位小数、海拔 1 位小数：
        {"namche-everest-view": {"points": [[lon, lat, ele], ...], "source": "..."}, ...}
    """
    if not refresh and OUT.exists():
        try:
            existing = json.loads(OUT.read_text())
        except (json.JSONDecodeError, OSError):
            existing = {}
        if all(leg_id in existing for leg_id, *_ in LEGS):
            print(f"{OUT} already has all {len(LEGS)} legs, skipping fetch")
            return

    result = {}
    for leg_id, start, goal, bbox, out_and_back in LEGS:
        print(f"leg {leg_id}:")
        leg = build_leg(leg_id, start, goal, bbox, out_and_back)
        result[leg_id] = {"points": leg["points"], "source": leg["source"]}
        print(f"  {len(leg['points'])} points, source={leg['source']}")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    import sys

    main(refresh="--refresh" in sys.argv)
