#!/usr/bin/env python3
"""
PathPal 数据校验脚本
读取 data/ 下全部 JSON 文件，校验课程设计要求
"""
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Entity node types for counting
ENTITY_TYPES = {
    "scenic_spot", "teaching_building", "office_building",
    "dormitory", "library", "canteen", "classroom_building",
    "building", "gate"
}

REQUIRED_MAP_IDS = {"MAP_CAMPUS_001", "MAP_SCENIC_001", "MAP_MIXED_001"}


def load_json(filename):
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


class Validator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = 0
        self.failed = 0

    def check(self, condition, message):
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(message)

    def warn(self, condition, message):
        if not condition:
            self.warnings.append(message)

    def report(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"Validation Summary: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"  FAILED checks: {self.failed}")
            for e in self.errors:
                print(f"    ✗ {e}")
        if self.warnings:
            print(f"  Warnings: {len(self.warnings)}")
            for w in self.warnings:
                print(f"    ⚠ {w}")
        if self.failed == 0:
            print("  All validation checks passed.")
        return self.failed


# ============================================================
# BFS 连通性检测（自行实现，不依赖 networkx）
# ============================================================
def check_connectivity(map_id, nodes, edges):
    """使用 BFS 检查图的连通性。图为无向图。"""
    node_set = {n["id"] for n in nodes}
    if not node_set:
        return True, 0, 0

    # 构建邻接表
    adj = defaultdict(list)
    for e in edges:
        if e["from"] in node_set and e["to"] in node_set:
            adj[e["from"]].append(e["to"])
            adj[e["to"]].append(e["from"])

    # BFS
    start = next(iter(node_set))
    visited = set()
    queue = [start]
    visited.add(start)
    while queue:
        u = queue.pop(0)
        for v in adj.get(u, []):
            if v not in visited:
                visited.add(v)
                queue.append(v)

    total = len(node_set)
    visited_count = len(visited)
    unreachable = total - visited_count
    return visited_count == total, total, unreachable


# ============================================================
# 校验函数
# ============================================================
def validate_destinations(destinations, maps, v: Validator):
    print("\n--- Destinations ---")
    map_ids = {m["id"] for m in maps}

    v.check(len(destinations) >= 200,
            f"destinations count >= 200 (actual: {len(destinations)})")
    print(f"  Destinations: {len(destinations)} {'OK' if len(destinations) >= 200 else 'FAIL'}")

    ids = [d["id"] for d in destinations]
    v.check(len(ids) == len(set(ids)), "destination IDs are unique")
    print(f"  Unique IDs: {'OK' if len(ids) == len(set(ids)) else 'FAIL'}")

    for d in destinations:
        v.check(d["type"] in ("campus", "attraction"),
                f"{d['id']}: type must be campus or attraction, got '{d['type']}'")
        v.check("internal_map_id" in d and d["internal_map_id"],
                f"{d['id']}: missing internal_map_id")
        v.check(d.get("internal_map_id", "") in map_ids,
                f"{d['id']}: internal_map_id '{d.get('internal_map_id')}' not found in internal_maps.json")
        v.check(d.get("popularity", 0) > 0,
                f"{d['id']}: popularity must be > 0")
        v.check(0 < d.get("rating", 0) <= 5.0,
                f"{d['id']}: rating must be in (0, 5.0]")
        if d["type"] == "campus":
            v.check(d.get("internal_map_id") in ("MAP_CAMPUS_001", "MAP_MIXED_001"),
                    f"{d['id']}: campus must use campus or mixed map, got {d.get('internal_map_id')}")
        elif d["type"] == "attraction":
            v.check(d.get("internal_map_id") in ("MAP_SCENIC_001", "MAP_MIXED_001"),
                    f"{d['id']}: attraction must use scenic or mixed map, got {d.get('internal_map_id')}")


def validate_internal_maps(maps, v: Validator):
    print("\n--- Internal Maps ---")
    v.check(len(maps) >= 3, f"internal_maps count >= 3 (actual: {len(maps)})")
    print(f"  Internal maps: {len(maps)} {'OK' if len(maps) >= 3 else 'FAIL'}")

    map_ids = set()
    for m in maps:
        v.check("id" in m and m["id"], f"map missing id")
        v.check(m.get("type") in ("campus", "attraction", "mixed"),
                f"{m.get('id')}: type must be campus/attraction/mixed")
        map_ids.add(m["id"])

    for required in REQUIRED_MAP_IDS:
        v.check(required in map_ids,
                f"required map '{required}' must exist")
    print(f"  Required maps present: {'OK' if REQUIRED_MAP_IDS.issubset(map_ids) else 'FAIL'}")


def validate_internal_nodes(nodes, maps, v: Validator):
    print("\n--- Internal Nodes ---")
    map_ids = {m["id"] for m in maps}

    node_ids = [n["id"] for n in nodes]
    v.check(len(node_ids) == len(set(node_ids)), "node IDs are unique")
    print(f"  Total nodes: {len(nodes)}")

    nodes_by_map = defaultdict(list)
    for n in nodes:
        v.check(n["map_id"] in map_ids,
                f"{n['id']}: map_id '{n['map_id']}' not found in internal_maps.json")
        v.check("latitude" in n and "longitude" in n,
                f"{n['id']}: missing coordinates")
        nodes_by_map[n["map_id"]].append(n)

    for mid in map_ids:
        map_nodes = nodes_by_map.get(mid, [])
        entities = [n for n in map_nodes if n["type"] in ENTITY_TYPES]
        v.check(len(entities) >= 20,
                f"{mid}: entity nodes {len(entities)} < 20 required")
        print(f"  {mid}: total={len(map_nodes)}, entities={len(entities)} "
              f"{'OK' if len(entities) >= 20 else 'FAIL'}")


def validate_internal_edges(edges, nodes, maps, v: Validator):
    print("\n--- Internal Edges ---")
    map_ids = {m["id"] for m in maps}
    node_by_id = {n["id"]: n for n in nodes}

    v.check(len(edges) >= 200,
            f"total edges {len(edges)} < 200 required")
    print(f"  Total edges: {len(edges)} {'OK' if len(edges) >= 200 else 'FAIL'}")

    edge_ids = [e["id"] for e in edges]
    v.check(len(edge_ids) == len(set(edge_ids)), "edge IDs are unique")

    edges_by_map = defaultdict(list)
    for e in edges:
        v.check(e["map_id"] in map_ids,
                f"{e['id']}: map_id '{e['map_id']}' not found")
        v.check(e["distance"] > 0,
                f"{e['id']}: distance must be > 0")
        v.check(0 < e.get("congestion", 0) <= 1,
                f"{e['id']}: congestion must be in (0, 1]")
        v.check(len(e.get("allowed_transport", [])) > 0,
                f"{e['id']}: allowed_transport must not be empty")
        v.check(e["from"] in node_by_id,
                f"{e['id']}: from node '{e['from']}' not found")
        v.check(e["to"] in node_by_id,
                f"{e['id']}: to node '{e['to']}' not found")
        if e["from"] in node_by_id and e["to"] in node_by_id:
            fn = node_by_id[e["from"]]
            tn = node_by_id[e["to"]]
            v.check(fn["map_id"] == tn["map_id"],
                    f"{e['id']}: from/to nodes are in different maps")
            v.check(e["map_id"] == fn["map_id"],
                    f"{e['id']}: edge.map_id != from node's map_id")

        # Transport constraints
        map_type = None
        for m in maps:
            if m["id"] == e["map_id"]:
                map_type = m["type"]
                break
        if map_type == "campus":
            v.check("sightseeing_car" not in e.get("allowed_transport", []),
                    f"{e['id']}: campus map must not allow sightseeing_car")
        elif map_type == "attraction":
            v.check("bike" not in e.get("allowed_transport", []),
                    f"{e['id']}: scenic map must not allow bike")

        edges_by_map[e["map_id"]].append(e)

    for mid in map_ids:
        cnt = len(edges_by_map.get(mid, []))
        print(f"  {mid}: {cnt} edges")


def validate_facilities(facilities, nodes, maps, v: Validator):
    print("\n--- Facilities ---")
    map_ids = {m["id"] for m in maps}
    node_by_id = {n["id"]: n for n in nodes}

    v.check(len(facilities) >= 50,
            f"facilities count {len(facilities)} < 50 required")
    print(f"  Total facilities: {len(facilities)} {'OK' if len(facilities) >= 50 else 'FAIL'}")

    fac_ids = [f["id"] for f in facilities]
    v.check(len(fac_ids) == len(set(fac_ids)), "facility IDs are unique")

    categories = set()
    for f in facilities:
        categories.add(f.get("category", ""))
        v.check(f["map_id"] in map_ids,
                f"{f['id']}: map_id '{f['map_id']}' not found")
        v.check(f["linked_node_id"] in node_by_id,
                f"{f['id']}: linked_node_id '{f['linked_node_id']}' not found")
        if f["linked_node_id"] in node_by_id:
            linked_node = node_by_id[f["linked_node_id"]]
            v.check(f["map_id"] == linked_node["map_id"],
                    f"{f['id']}: facility.map_id != linked node's map_id")

    v.check(len(categories) >= 10,
            f"facility categories {len(categories)} < 10 required")
    print(f"  Categories ({len(categories)}): {sorted(categories)} "
          f"{'OK' if len(categories) >= 10 else 'FAIL'}")


def validate_users(users, v: Validator):
    print("\n--- Users ---")
    v.check(len(users) >= 10,
            f"users count {len(users)} < 10 required")
    print(f"  Users: {len(users)} {'OK' if len(users) >= 10 else 'FAIL'}")

    uids = [u["id"] for u in users]
    v.check(len(uids) == len(set(uids)), "user IDs are unique")

    for u in users:
        v.check(len(u.get("interests", [])) > 0,
                f"{u['id']}: interests must not be empty")
        v.check(len(u.get("favorite_categories", [])) > 0,
                f"{u['id']}: favorite_categories must not be empty")
        v.check(len(u.get("preferred_tags", [])) > 0,
                f"{u['id']}: preferred_tags must not be empty")


def validate_indoor_graphs(indoor_data, v: Validator):
    print("\n--- Indoor Graphs ---")
    indoor_maps = indoor_data.get("indoor_maps", [])
    v.check(len(indoor_maps) >= 1,
            f"indoor_maps count {len(indoor_maps)} < 1 required")
    print(f"  Indoor buildings: {len(indoor_maps)} {'OK' if len(indoor_maps) >= 1 else 'FAIL'}")

    for bld in indoor_maps:
        nodes = bld.get("nodes", [])
        edges = bld.get("edges", [])
        node_ids = {n["id"] for n in nodes}
        v.check(len(nodes) > 0,
                f"{bld.get('building_id')}: must have nodes")
        for e in edges:
            v.check(e["from"] in node_ids,
                    f"{bld.get('building_id')}: indoor edge from '{e['from']}' not found")
            v.check(e["to"] in node_ids,
                    f"{bld.get('building_id')}: indoor edge to '{e['to']}' not found")


def validate_connectivity(nodes_list, edges_list, v: Validator):
    print("\n--- Connectivity ---")
    nodes_by_map = defaultdict(list)
    for n in nodes_list:
        nodes_by_map[n["map_id"]].append(n)

    edges_by_map = defaultdict(list)
    for e in edges_list:
        edges_by_map[e["map_id"]].append(e)

    all_connected = True
    for map_id in sorted(nodes_by_map.keys()):
        mnodes = nodes_by_map[map_id]
        medges = edges_by_map[map_id]
        is_connected, total, unreachable = check_connectivity(map_id, mnodes, medges)
        if is_connected:
            print(f"  {map_id}: connected (total nodes: {total})")
        else:
            all_connected = False
            print(f"  {map_id}: DISCONNECTED! {unreachable}/{total} nodes unreachable")
        v.check(is_connected,
                f"{map_id}: graph is not fully connected ({unreachable}/{total} unreachable)")


def print_statistics(destinations, maps, nodes, edges, facilities, users, indoor_data):
    print(f"\n{'='*50}")
    print("PathPal Data Validation Report")
    print("=" * 50)

    nodes_by_map = Counter(n["map_id"] for n in nodes)
    edges_by_map = Counter(e["map_id"] for e in edges)
    facs_by_map = Counter(f["map_id"] for f in facilities)
    entities_by_map = defaultdict(int)
    for n in nodes:
        if n["type"] in ENTITY_TYPES:
            entities_by_map[n["map_id"]] += 1

    campus_count = sum(1 for d in destinations if d["type"] == "campus")
    attraction_count = sum(1 for d in destinations if d["type"] == "attraction")

    print(f"\nDestinations: {len(destinations)} (campus: {campus_count}, attraction: {attraction_count})")
    print(f"Internal maps: {len(maps)}")
    print(f"Internal nodes: {len(nodes)}")
    print(f"Internal edges: {len(edges)}")
    print(f"Facilities: {len(facilities)}")
    print(f"Facility categories: {len(set(f['category'] for f in facilities))}")
    print(f"Users: {len(users)}")
    indoor_maps = indoor_data.get("indoor_maps", [])
    print(f"Indoor buildings: {len(indoor_maps)}")

    print(f"\nPer-map details:")
    for mid in sorted(nodes_by_map.keys()):
        print(f"  {mid}: nodes={nodes_by_map[mid]} (entities={entities_by_map[mid]}), "
              f"edges={edges_by_map.get(mid, 0)}, facilities={facs_by_map.get(mid, 0)}")


def main():
    print("=" * 50)
    print("PathPal Data Validator")
    print("=" * 50)

    # Load all data
    try:
        destinations = load_json("destinations.json")
        maps = load_json("internal_maps.json")
        nodes = load_json("internal_nodes.json")
        edges = load_json("internal_edges.json")
        facilities = load_json("facilities.json")
        users = load_json("users.json")
        indoor_data = load_json("indoor_graphs.json")
    except FileNotFoundError as e:
        print(f"ERROR: Data file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return 1

    v = Validator()

    # Print statistics first
    print_statistics(destinations, maps, nodes, edges, facilities, users, indoor_data)

    # Run all validations
    validate_destinations(destinations, maps, v)
    validate_internal_maps(maps, v)
    validate_internal_nodes(nodes, maps, v)
    validate_internal_edges(edges, nodes, maps, v)
    validate_facilities(facilities, nodes, maps, v)
    validate_users(users, v)
    validate_indoor_graphs(indoor_data, v)
    validate_connectivity(nodes, edges, v)

    # Report
    failed = v.report()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
