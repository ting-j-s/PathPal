"""
PathPal 室内导航 Dijkstra 算法
专用于室内图：边权 = distance，无向图，不依赖 outdoor 边字段。
"""
import heapq
from collections import defaultdict

INF = float("inf")


def indoor_dijkstra(building, start_id, end_id):
    """
    室内最短距离路径。

    Args:
        building: dict，包含 nodes 和 edges
        start_id: 起始节点 ID
        end_id: 终点节点 ID

    Returns:
        dict: {
            "reachable": bool,
            "path": [node_id, ...],
            "distance": float,
            "nodes": [node_dict, ...],   # 路径上每个节点的完整信息
            "edges": [edge_dict, ...],   # 路径上每条边的完整信息
            "steps": [step_dict, ...],
            "floor_paths": {floor: [node_id, ...]},
        }
    """
    nodes = building.get("nodes", [])
    edges = building.get("edges", [])

    node_map = {n["id"]: n for n in nodes}

    # 构建无向邻接表
    adj = defaultdict(list)
    edge_map = {}  # (u, v) -> edge
    for e in edges:
        u, v = e["from"], e["to"]
        adj[u].append((v, e))
        adj[v].append((u, e))
        edge_map[(u, v)] = e
        edge_map[(v, u)] = e

    if start_id not in node_map:
        raise ValueError(f"Start node not found: {start_id}")
    if end_id not in node_map:
        raise ValueError(f"End node not found: {end_id}")

    # Dijkstra
    dist = {nid: INF for nid in node_map}
    prev = {nid: None for nid in node_map}
    prev_edge = {nid: None for nid in node_map}

    dist[start_id] = 0
    pq = [(0, start_id)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == end_id:
            break
        for v, edge in adj[u]:
            w = edge.get("distance", 1)
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                prev_edge[v] = edge
                heapq.heappush(pq, (nd, v))

    if dist[end_id] == INF:
        return {
            "reachable": False,
            "path": [],
            "distance": 0,
            "nodes": [],
            "edges": [],
            "steps": [],
            "floor_paths": {},
        }

    # 回溯路径
    path = []
    path_nodes = []
    path_edges = []
    cur = end_id
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    for nid in path:
        path_nodes.append(node_map[nid])

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        e = edge_map.get((u, v))
        if e:
            path_edges.append(e)

    # 生成步骤
    steps = _generate_steps(path_nodes, path_edges)

    # 按楼层分组
    floor_paths = defaultdict(list)
    for nid in path:
        nd = node_map[nid]
        floor_paths[str(nd.get("floor", 1))].append(nid)

    return {
        "reachable": True,
        "path": path,
        "distance": round(dist[end_id], 1),
        "nodes": path_nodes,
        "edges": path_edges,
        "steps": steps,
        "floor_paths": dict(floor_paths),
    }


def _generate_steps(nodes, edges):
    """根据路径节点和边生成中文步骤描述。"""
    steps = []
    if not nodes:
        return steps

    # 起点
    steps.append({
        "step": 1,
        "description": f"从{_node_label(nodes[0])}出发",
        "type": "start",
    })

    step_no = 2
    for i, edge in enumerate(edges):
        from_node = nodes[i] if i < len(nodes) else None
        to_node = nodes[i + 1] if i + 1 < len(nodes) else None
        etype = edge.get("type", "corridor")
        dist = edge.get("distance", 0)

        if etype == "elevator":
            from_floor = from_node.get("floor", "?") if from_node else "?"
            to_floor = to_node.get("floor", "?") if to_node else "?"
            desc = f"乘电梯从{from_floor}层到{to_floor}层（{dist}米）"
        elif etype == "stairs":
            from_floor = from_node.get("floor", "?") if from_node else "?"
            to_floor = to_node.get("floor", "?") if to_node else "?"
            desc = f"走楼梯从{from_floor}层到{to_floor}层（{dist}米）"
        elif etype == "doorway":
            desc = f"通过门口前往{_node_label(to_node)}（{dist}米）"
        else:
            desc = f"沿走廊前往{_node_label(to_node)}（{dist}米）"

        steps.append({
            "step": step_no,
            "description": desc,
            "type": etype,
            "from": edge.get("from"),
            "to": edge.get("to"),
            "distance": dist,
        })
        step_no += 1

    # 终点
    steps.append({
        "step": step_no,
        "description": f"到达{_node_label(nodes[-1])}",
        "type": "end",
    })

    return steps


def _node_label(node):
    """节点用于步骤描述的标签。"""
    ntype = node.get("type", "")
    name = node.get("name", node.get("id", ""))
    floor = node.get("floor", "")
    if floor:
        return f"{name}({floor}F)"
    return name
