#!/usr/bin/env python3
"""
连接 OSM 导入图中的不连通组件。
为每个真实地图添加 bridge 边，使所有节点连通。
"""
import json
import math
import sys
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

R = 6371000


def haversine_distance(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_components(nodes_map, edges):
    """返回连通组件列表，每个为 node_id 集合。"""
    node_ids = set(nodes_map.keys())
    adj = defaultdict(list)
    for e in edges:
        if e["from"] in node_ids and e["to"] in node_ids:
            adj[e["from"]].append(e["to"])
            adj[e["to"]].append(e["from"])

    visited_all = set()
    components = []

    for start in node_ids:
        if start in visited_all:
            continue
        visited = set()
        queue = [start]
        visited.add(start)
        while queue:
            u = queue.pop(0)
            for v in adj.get(u, []):
                if v not in visited:
                    visited.add(v)
                    queue.append(v)
        visited_all.update(visited)
        components.append(visited)

    components.sort(key=len, reverse=True)
    return components


def connect_components(map_id, nodes_data, edges_data):
    """通过添加 bridge 边连接所有不连通组件。"""
    map_nodes = {n["id"]: n for n in nodes_data if n["map_id"] == map_id}
    map_edges = [e for e in edges_data if e["map_id"] == map_id]

    components = find_components(map_nodes, map_edges)
    print(f"  Components: {len(components)}")

    if len(components) <= 1:
        print(f"  Already fully connected!")
        return 0

    bridge_count = 0
    main_comp = components[0]

    for i in range(1, len(components)):
        small_comp = components[i]

        # 找两个组件之间最近的一对节点
        best_dist = float('inf')
        best_pair = (None, None)

        for n1_id in main_comp:
            n1 = map_nodes[n1_id]
            lat1, lng1 = n1["latitude"], n1["longitude"]
            for n2_id in small_comp:
                n2 = map_nodes[n2_id]
                d = haversine_distance(lat1, lng1, n2["latitude"], n2["longitude"])
                if d < best_dist:
                    best_dist = d
                    best_pair = (n1_id, n2_id)

        if best_pair[0] is None:
            continue

        n1_id, n2_id = best_pair
        n1 = map_nodes[n1_id]
        n2 = map_nodes[n2_id]

        # 创建双向 bridge 边
        prefix = "BUP" if "BUPT" in map_id else "TSR"
        base_id = f"EDGE_BRIDGE_{prefix}_{i:03d}"
        geom = [[n1["latitude"], n1["longitude"]],
                [n2["latitude"], n2["longitude"]]]

        edge_a = {
            "id": base_id + "a",
            "map_id": map_id,
            "from": n1_id,
            "to": n2_id,
            "name": "连接道路",
            "distance": round(best_dist, 1),
            "congestion": 0.95,
            "ideal_speed_walk": 1.33,
            "ideal_speed_bike": 3.67,
            "ideal_speed_sightseeing_car": 0 if map_id == "MAP_BUPT_REAL" else 5.0,
            "allowed_transport": ["walk"] if map_id == "MAP_SCENIC_REAL" else ["walk", "bike"],
            "road_type": "path",
            "geometry": geom,
        }
        edge_b = dict(edge_a)
        edge_b["id"] = base_id + "b"
        edge_b["from"] = n2_id
        edge_b["to"] = n1_id
        edge_b["geometry"] = [geom[1], geom[0]]

        edges_data.append(edge_a)
        edges_data.append(edge_b)
        bridge_count += 2

        # 合并到 main_comp
        main_comp.update(small_comp)

        print(f"    Bridge {i}: {n1['name']} ↔ {n2['name']} ({best_dist:.1f}m)")

    print(f"  Added {bridge_count} bridge edges")

    # 验证连通性
    final_components = find_components(map_nodes, edges_data)
    print(f"  Final components: {len(final_components)}")

    return bridge_count


def main():
    print("=" * 50)
    print("Connect OSM Graph Components")
    print("=" * 50)

    with open(DATA_DIR / "internal_nodes.json", "r", encoding="utf-8") as f:
        nodes = json.load(f)
    with open(DATA_DIR / "internal_edges.json", "r", encoding="utf-8") as f:
        edges = json.load(f)

    total_bridges = 0

    for map_id in ["MAP_BUPT_REAL", "MAP_SCENIC_REAL"]:
        print(f"\n{map_id}:")
        bridges = connect_components(map_id, nodes, edges)
        total_bridges += bridges

    # Write back
    edges.sort(key=lambda x: x["id"])
    with open(DATA_DIR / "internal_edges.json", "w", encoding="utf-8") as f:
        json.dump(edges, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Added {total_bridges} total bridge edges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
