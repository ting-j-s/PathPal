"""
PathPal Dijkstra 最短路径算法（自行实现，不依赖 networkx）

支持多种权函数：
- shortest_distance: 边权 = distance
- shortest_time: 边权 = time (指定交通工具)
- mixed_time: 每条边自动选最快交通工具
"""
import math

INF = float("inf")

# 景区类型的交通工具约束
CAMPUS_TRANSPORTS = {"walk", "bike"}
ATTRACTION_TRANSPORTS = {"walk", "sightseeing_car"}


# ============================================================
# 边时间计算
# ============================================================
def calculate_edge_time(edge, transport):
    """
    计算边在指定交通工具下的通行时间。
    返回 {"time": ..., "ideal_speed": ..., "real_speed": ..., "transport": ...}
    如果不可通行，返回 None。
    """
    if transport not in edge.get("allowed_transport", []):
        return None

    speed_map = {
        "walk": "ideal_speed_walk",
        "bike": "ideal_speed_bike",
        "sightseeing_car": "ideal_speed_sightseeing_car",
    }

    speed_key = speed_map.get(transport)
    if speed_key is None:
        return None

    ideal_speed = edge.get(speed_key, 0)
    if ideal_speed is None or ideal_speed <= 0:
        return None

    congestion = edge.get("congestion", 1.0)
    real_speed = congestion * ideal_speed
    if real_speed <= 0:
        return None

    distance = edge["distance"]
    time = distance / real_speed

    return {
        "time": time,
        "ideal_speed": ideal_speed,
        "real_speed": real_speed,
        "transport": transport,
    }


def choose_best_transport_for_edge(edge, destination_type):
    """
    为一条边选择最佳交通工具（耗时最短）。
    destination_type: "campus" | "attraction" | "mixed"
    返回时间信息 dict，或 None（无可用交通工具）。
    """
    if destination_type == "campus":
        candidates = CAMPUS_TRANSPORTS
    elif destination_type == "attraction":
        candidates = ATTRACTION_TRANSPORTS
    else:  # mixed
        candidates = {"walk", "bike", "sightseeing_car"}

    best = None
    best_time = INF

    for transport in candidates:
        result = calculate_edge_time(edge, transport)
        if result is not None and result["time"] < best_time:
            best_time = result["time"]
            best = result

    return best


# ============================================================
# 通用 Dijkstra
# ============================================================
def dijkstra(graph, start, end, weight_func):
    """
    通用 Dijkstra 最短路径。

    参数:
        graph: Graph 对象
        start: 起点 node_id
        end: 终点 node_id
        weight_func(edge) -> {"weight": float, "transport": ..., "time": ..., ...}
            返回包含 "weight" 键的 dict。

    返回:
        {
            "path": [node_id, ...],
            "total_distance": float,
            "total_time": float,
            "segments": [{from, to, from_name, to_name, distance, transport,
                          congestion, ideal_speed, real_speed, time}, ...],
            "reachable": bool
        }
    """
    if not graph.has_node(start):
        raise ValueError(f"Start node not found: {start}")
    if not graph.has_node(end):
        raise ValueError(f"End node not found: {end}")

    # 初始化
    dist = {}
    prev = {}
    prev_edge = {}
    visited = set()

    for node_id in graph.nodes:
        dist[node_id] = INF
        prev[node_id] = None
        prev_edge[node_id] = None
    dist[start] = 0

    unvisited = list(graph.nodes.keys())

    while unvisited:
        # 找到未访问中距离最小的节点
        u = None
        u_dist = INF
        for candidate in unvisited:
            if dist[candidate] < u_dist:
                u_dist = dist[candidate]
                u = candidate

        if u is None or u_dist == INF:
            break

        if u == end:
            break

        unvisited.remove(u)
        visited.add(u)

        for edge in graph.get_neighbors(u):
            # 判断边的方向：from→to 或 to→from（无向图）
            if edge["from"] == u:
                v = edge["to"]
            elif edge["to"] == u and not graph.directed:
                v = edge["from"]
            else:
                continue

            if v in visited:
                continue

            weight_info = weight_func(edge)
            if weight_info is None:
                continue

            new_dist = u_dist + weight_info["weight"]
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                prev_edge[v] = (edge, weight_info)

    # 构建结果
    if dist[end] == INF:
        return {
            "path": [],
            "total_distance": INF,
            "total_time": INF,
            "segments": [],
            "reachable": False,
        }

    # 回溯路径
    path = []
    curr = end
    while curr is not None:
        path.append(curr)
        curr = prev[curr]
    path.reverse()

    # 构建 segments
    segments = []
    total_distance = 0
    total_time = 0

    for i in range(len(path) - 1):
        f = path[i]
        t = path[i + 1]
        edge, weight_info = prev_edge[t]
        seg_distance = edge["distance"]
        total_distance += seg_distance

        seg_time = weight_info.get("time", 0)
        total_time += seg_time

        seg_geometry = _get_segment_geometry(edge, f, t)

        segments.append({
            "from": f,
            "to": t,
            "from_name": graph.get_node_name(f),
            "to_name": graph.get_node_name(t),
            "distance": seg_distance,
            "transport": weight_info.get("transport"),
            "congestion": edge.get("congestion"),
            "ideal_speed": weight_info.get("ideal_speed"),
            "real_speed": weight_info.get("real_speed"),
            "time": seg_time,
            "geometry": seg_geometry,
        })

    return {
        "path": path,
        "total_distance": total_distance,
        "total_time": total_time,
        "segments": segments,
        "reachable": True,
    }


# ============================================================
# 单源全节点 Dijkstra
# ============================================================
def dijkstra_all_distances(graph, start, weight_func=None):
    """
    从 start 出发计算到图中所有节点的最短距离（单源 Dijkstra）。

    参数:
        graph: Graph 对象
        start: 起点 node_id
        weight_func(edge) -> {"weight": float, ...} | None
            默认使用距离边权。

    返回:
        {
            "dist": {node_id: distance},
            "prev": {node_id: previous_node_id},
            "prev_edge": {node_id: (edge, weight_info)}
        }
    """
    if weight_func is None:
        weight_func = _weight_distance

    if not graph.has_node(start):
        raise ValueError(f"Start node not found: {start}")

    dist = {}
    prev = {}
    prev_edge = {}

    for node_id in graph.nodes:
        dist[node_id] = INF
        prev[node_id] = None
        prev_edge[node_id] = None
    dist[start] = 0

    unvisited = list(graph.nodes.keys())

    while unvisited:
        u = None
        u_dist = INF
        for candidate in unvisited:
            if dist[candidate] < u_dist:
                u_dist = dist[candidate]
                u = candidate

        if u is None or u_dist == INF:
            break

        unvisited.remove(u)

        for edge in graph.get_neighbors(u):
            if edge["from"] == u:
                v = edge["to"]
            elif edge["to"] == u and not graph.directed:
                v = edge["from"]
            else:
                continue

            if v not in unvisited:
                continue

            weight_info = weight_func(edge)
            if weight_info is None:
                continue

            new_dist = u_dist + weight_info["weight"]
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                prev_edge[v] = (edge, weight_info)

    return {"dist": dist, "prev": prev, "prev_edge": prev_edge}


def reconstruct_path_from_prev(prev, start, end):
    """
    根据 prev 指针回溯路径。

    返回:
        [node_id, ...] 或 [] (不可达)
    """
    if start == end:
        return [start]
    if prev.get(end) is None and start != end:
        return []
    path = []
    curr = end
    while curr is not None:
        path.append(curr)
        curr = prev.get(curr)
    path.reverse()
    # 验证回溯到了 start
    if not path or path[0] != start:
        return []
    return path


def reconstruct_segments_from_prev(graph, prev, prev_edge, start, end):
    """
    根据 prev / prev_edge 指针还原路径的 segments、总距离、总时间。

    返回:
        {
            "path": [node_id, ...],
            "segments": [...],
            "total_distance": float,
            "total_time": float,
        }
    """
    path = reconstruct_path_from_prev(prev, start, end)

    if not path:
        return {
            "path": [],
            "segments": [],
            "total_distance": INF,
            "total_time": INF,
        }

    if len(path) == 1:
        return {
            "path": path,
            "segments": [],
            "total_distance": 0,
            "total_time": 0,
        }

    segments = []
    total_distance = 0
    total_time = 0

    for i in range(len(path) - 1):
        f = path[i]
        t = path[i + 1]
        edge_and_info = prev_edge.get(t)
        if edge_and_info is None:
            # 缺少边信息（数据异常）
            return {
                "path": [],
                "segments": [],
                "total_distance": INF,
                "total_time": INF,
            }
        edge, weight_info = edge_and_info

        seg_distance = edge["distance"]
        total_distance += seg_distance
        seg_time = weight_info.get("time", 0)
        total_time += seg_time
        seg_geometry = _get_segment_geometry(edge, f, t)

        segments.append({
            "from": f,
            "to": t,
            "from_name": graph.get_node_name(f),
            "to_name": graph.get_node_name(t),
            "distance": seg_distance,
            "transport": weight_info.get("transport"),
            "congestion": edge.get("congestion"),
            "ideal_speed": weight_info.get("ideal_speed"),
            "real_speed": weight_info.get("real_speed"),
            "time": seg_time,
            "geometry": seg_geometry,
        })

    return {
        "path": path,
        "segments": segments,
        "total_distance": total_distance,
        "total_time": total_time,
    }


# ============================================================
# 距离最短策略
# ============================================================
def _weight_distance(edge):
    return {
        "weight": edge["distance"],
        "transport": "walk",
        "time": _estimate_time(edge, "walk"),
        "ideal_speed": edge.get("ideal_speed_walk"),
        "real_speed": edge.get("congestion", 1.0) * edge.get("ideal_speed_walk", 1.2),
    }


def _estimate_time(edge, transport):
    """估算边的通行时间，用于非时间策略中的参考时间。"""
    result = calculate_edge_time(edge, transport)
    if result:
        return result["time"]
    return edge["distance"] / 1.2  # fallback to walk speed


def dijkstra_shortest_distance(graph, start, end):
    """边权 = distance，最短距离路径。"""
    return dijkstra(graph, start, end, _weight_distance)


# ============================================================
# 指定交通工具时间最短策略
# ============================================================
def _make_weight_time(transport):
    def weight_func(edge):
        result = calculate_edge_time(edge, transport)
        if result is None:
            return None
        return {
            "weight": result["time"],
            **result,
        }
    return weight_func


def dijkstra_shortest_time(graph, start, end, transport="walk"):
    """边权 = 指定交通工具的 time。不可通行的边跳过。"""
    return dijkstra(graph, start, end, _make_weight_time(transport))


# ============================================================
# 混合交通时间最短策略
# ============================================================
def _make_weight_mixed(destination_type):
    def weight_func(edge):
        best = choose_best_transport_for_edge(edge, destination_type)
        if best is None:
            return None
        return {
            "weight": best["time"],
            **best,
        }
    return weight_func


def dijkstra_mixed_time(graph, start, end, destination_type):
    """
    混合交通策略：每条边自动选择可用交通工具中耗时最短的。
    destination_type: "campus" | "attraction" | "mixed"
    """
    return dijkstra(graph, start, end, _make_weight_mixed(destination_type))


# ============================================================
# 多点路线（贪心 TSP 近似）
# ============================================================
def _get_segment_geometry(edge, from_node_id, to_node_id):
    """
    获取 segment 的 geometry。
    如果 edge 有 geometry，根据方向返回正向或反向。
    如果 edge 没有 geometry，用 from/to 坐标构建两点 geometry。
    """
    geom = edge.get("geometry")
    if geom and len(geom) >= 2:
        # 检查方向：geometry[0] 应对应 from_node
        if edge["from"] == from_node_id:
            return geom
        else:
            return list(reversed(geom))

    # Fallback: 用 edge 的 from/to 两点构建
    from_coord = edge.get("from_coord")
    to_coord = edge.get("to_coord")
    if from_coord and to_coord:
        if edge["from"] == from_node_id:
            return [from_coord, to_coord]
        else:
            return [to_coord, from_coord]

    return None


def extract_route_geometry(segments):
    """
    从 segments 的 geometry 拼接完整 route_geometry。
    相邻 segment 间去除重复的连接点。
    """
    if not segments:
        return []

    all_points = []
    for i, seg in enumerate(segments):
        geom = seg.get("geometry")
        if not geom or len(geom) < 2:
            continue

        if i == 0:
            all_points.extend(geom)
        else:
            # 跳过第一个点（与前一段的最后一个点重复）
            all_points.extend(geom[1:])

    return all_points


def multi_point_route(graph, start, targets, strategy="shortest_distance",
                       destination_type=None):
    """
    贪心 TSP 近似：从 start 出发，每次选择距离最近的未访问目标，
    访问全部后返回 start。

    参数:
        graph: Graph 对象
        start: 起点 node_id（同时也是终点）
        targets: 目标 node_id 列表
        strategy: "shortest_distance" | "shortest_time" | "mixed_time"
        destination_type: 用于 mixed_time 策略

    返回:
        {
            "path": [...],
            "segments": [...],
            "total_distance": float,
            "total_time": float,
            "visit_order": [...],
            "reachable": bool
        }
    """
    if not targets:
        return {
            "path": [start],
            "segments": [],
            "total_distance": 0,
            "total_time": 0,
            "visit_order": [],
            "reachable": True,
        }

    # 选择权函数 —— 多目标场景下，时间策略统一使用 mixed（自动选最快交通工具），
    # 避免 campus 下 bike 无法到达 walk-only 路段导致节点不可达。
    if strategy == "shortest_distance":
        route_fn = dijkstra_shortest_distance
        compare_key = "total_distance"
    elif strategy in ("shortest_time", "mixed_time"):
        def route_fn(g, s, e):
            return dijkstra_mixed_time(g, s, e, destination_type)
        compare_key = "total_time"
    else:
        route_fn = dijkstra_shortest_distance
        compare_key = "total_distance"

    remaining = set(targets)
    current = start
    visit_order = []
    all_path = []
    all_segments = []
    total_distance = 0
    total_time = 0

    while remaining:
        # 找最近的未访问目标（按对应策略比较距离/时间）
        best_target = None
        best_val = INF
        best_result = None

        for t in remaining:
            result = route_fn(graph, current, t)
            if result["reachable"] and result[compare_key] < best_val:
                best_val = result[compare_key]
                best_target = t
                best_result = result

        if best_target is None:
            return {
                "path": all_path,
                "segments": all_segments,
                "total_distance": total_distance,
                "total_time": total_time,
                "visit_order": visit_order,
                "reachable": False,
            }

        # 合并路径（避免重复添加连接点）
        if all_path:
            all_path.extend(best_result["path"][1:])
        else:
            all_path.extend(best_result["path"])

        all_segments.extend(best_result["segments"])
        total_distance += best_result["total_distance"]
        total_time += best_result["total_time"]
        visit_order.append(best_target)
        remaining.remove(best_target)
        current = best_target

    # 返回起点
    if current != start:
        result = route_fn(graph, current, start)
        if result["reachable"]:
            for seg in result["segments"]:
                seg["is_return"] = True
            all_path.extend(result["path"][1:])
            all_segments.extend(result["segments"])
            total_distance += result["total_distance"]
            total_time += result["total_time"]

    return {
        "path": all_path,
        "segments": all_segments,
        "total_distance": total_distance,
        "total_time": total_time,
        "visit_order": visit_order,
        "reachable": True,
    }
