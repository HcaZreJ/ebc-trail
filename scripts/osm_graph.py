"""OSM 步道图论：从 Overpass way 元素建无向图、Dijkstra 求最短路、最近节点查找。

gap_legs.py 用这里的三个函数把 Overpass 返回的步道几何拼成可走的点序列。
"""
import heapq
import math

from geo import haversine_m


def build_graph(overpass_json):
    """Overpass `out body geom` 的 way 元素 → ({node_id: (lat, lon)}, {node_id: [(邻居, 边长 m)]})。"""
    nodes = {}
    adj = {}
    for el in overpass_json.get("elements", []):
        if el.get("type") != "way":
            continue
        node_ids = el.get("nodes", [])
        geometry = el.get("geometry", [])
        for node_id, pt in zip(node_ids, geometry):
            if pt is None:
                continue
            nodes[node_id] = (pt["lat"], pt["lon"])
            adj.setdefault(node_id, [])
        for i in range(len(node_ids) - 1):
            a, b = node_ids[i], node_ids[i + 1]
            pa, pb = geometry[i], geometry[i + 1]
            if pa is None or pb is None:
                continue
            dist = haversine_m(pa["lat"], pa["lon"], pb["lat"], pb["lon"])
            adj.setdefault(a, []).append((b, dist))
            adj.setdefault(b, []).append((a, dist))
    return nodes, adj


def shortest_path(nodes, adj, start_id, goal_id):
    """Dijkstra 求 start_id → goal_id 的点序列 [(lat, lon)]；不连通返回 None。"""
    if start_id not in nodes:
        raise KeyError(start_id)
    if goal_id not in nodes:
        raise KeyError(goal_id)
    if start_id == goal_id:
        return [nodes[start_id]]

    dist = {start_id: 0.0}
    prev = {}
    visited = set()
    heap = [(0.0, start_id)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == goal_id:
            break
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    if goal_id not in dist:
        return None
    path_ids = [goal_id]
    while path_ids[-1] != start_id:
        path_ids.append(prev[path_ids[-1]])
    path_ids.reverse()
    return [nodes[i] for i in path_ids]


def nearest_node(nodes, point):
    """取距 point=(lat, lon) 最近的图节点 id；nodes 为空返回 None。"""
    lat, lon = point
    best_id, best_dist = None, math.inf
    for node_id, (nlat, nlon) in nodes.items():
        d = haversine_m(lat, lon, nlat, nlon)
        if d < best_dist:
            best_dist, best_id = d, node_id
    return best_id
