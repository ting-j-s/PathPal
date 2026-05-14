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
REAL_MAP_IDS = {"MAP_BUPT_REAL", "MAP_BNU_REAL", "MAP_SCENIC_REAL",
                "MAP_CAMPUS_OSM", "MAP_SCENIC_OSM"}
ALL_MAP_IDS = REQUIRED_MAP_IDS | REAL_MAP_IDS


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
    map_ids = {m.get("map_id") or m.get("id") for m in maps}

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
            v.check(d.get("internal_map_id") in ("MAP_CAMPUS_001", "MAP_MIXED_001",
                       "MAP_BUPT_REAL", "MAP_BNU_REAL", "MAP_CAMPUS_OSM"),
                    f"{d['id']}: campus must use campus or mixed map, got {d.get('internal_map_id')}")
        elif d["type"] == "attraction":
            v.check(d.get("internal_map_id") in ("MAP_SCENIC_001", "MAP_MIXED_001",
                       "MAP_SCENIC_REAL", "MAP_SCENIC_OSM"),
                    f"{d['id']}: attraction must use scenic or mixed map, got {d.get('internal_map_id')}")


def validate_internal_maps(maps, v: Validator):
    print("\n--- Internal Maps ---")
    v.check(len(maps) >= 8, f"internal_maps count >= 8 (actual: {len(maps)})")
    print(f"  Internal maps: {len(maps)} {'OK' if len(maps) >= 5 else 'FAIL'}")

    map_ids = set()
    for m in maps:
        mid = m.get("map_id") or m.get("id")
        v.check(mid, f"map missing map_id")
        v.check(m.get("type") in ("campus", "attraction", "mixed"),
                f"{mid}: type must be campus/attraction/mixed")
        map_ids.add(mid)

        # New required fields
        v.check("source" in m, f"{mid}: missing 'source' field")
        v.check("is_real_map" in m, f"{mid}: missing 'is_real_map' field")
        v.check("show_tile" in m, f"{mid}: missing 'show_tile' field")
        v.check("center" in m, f"{mid}: missing 'center' field")
        v.check("tile_note" in m, f"{mid}: missing 'tile_note' field")

        # Consistency: show_tile=true → is_real_map must be true
        if m.get("show_tile") is True:
            v.check(m.get("is_real_map") is True,
                    f"{mid}: show_tile=true but is_real_map is not true")
            v.check(m.get("source") in ("openstreetmap", "real_osm", "openstreetmap_vector", "manual_osm_aligned"),
                    f"{mid}: show_tile=true but source '{m.get('source')}' is not recognized")

        # Consistency: show_tile=false → is_real_map should be false
        if m.get("show_tile") is False:
            v.check(m.get("is_real_map") is False,
                    f"{mid}: show_tile=false but is_real_map is true")

    # Required maps must exist
    for required in ALL_MAP_IDS:
        v.check(required in map_ids,
                f"required map '{required}' must exist")
    print(f"  Required maps present: {'OK' if ALL_MAP_IDS.issubset(map_ids) else 'FAIL'}")

    # MAP_BUPT_REAL specific checks
    bupt = next((m for m in maps if (m.get("map_id") or m.get("id")) == "MAP_BUPT_REAL"), None)
    if bupt:
        v.check(bupt.get("type") == "campus",
                f"MAP_BUPT_REAL: type must be 'campus', got '{bupt.get('type')}'")
        v.check("sightseeing_car" not in bupt.get("supported_transports", []),
                "MAP_BUPT_REAL: campus must not support sightseeing_car")

    # MAP_SCENIC_REAL specific checks
    scenic = next((m for m in maps if (m.get("map_id") or m.get("id")) == "MAP_SCENIC_REAL"), None)
    if scenic:
        v.check(scenic.get("type") == "attraction",
                f"MAP_SCENIC_REAL: type must be 'attraction', got '{scenic.get('type')}'")
        v.check("bike" not in scenic.get("supported_transports", []),
                "MAP_SCENIC_REAL: scenic must not support bike")

    # MAP_BNU_REAL specific checks
    bnu = next((m for m in maps if (m.get("map_id") or m.get("id")) == "MAP_BNU_REAL"), None)
    if bnu:
        v.check(bnu.get("type") == "campus",
                f"MAP_BNU_REAL: type must be 'campus', got '{bnu.get('type')}'")
        v.check("sightseeing_car" not in bnu.get("supported_transports", []),
                "MAP_BNU_REAL: campus must not support sightseeing_car")

    # MAP_CAMPUS_OSM specific checks (school OSM template)
    campus_osm = next((m for m in maps if (m.get("map_id") or m.get("id")) == "MAP_CAMPUS_OSM"), None)
    if campus_osm:
        v.check(campus_osm.get("type") == "campus",
                f"MAP_CAMPUS_OSM: type must be 'campus', got '{campus_osm.get('type')}'")
        v.check("sightseeing_car" not in campus_osm.get("supported_transports", []),
                "MAP_CAMPUS_OSM: campus must not support sightseeing_car")

    # MAP_SCENIC_OSM specific checks (scenic OSM template)
    scenic_osm = next((m for m in maps if (m.get("map_id") or m.get("id")) == "MAP_SCENIC_OSM"), None)
    if scenic_osm:
        v.check(scenic_osm.get("type") == "attraction",
                f"MAP_SCENIC_OSM: type must be 'attraction', got '{scenic_osm.get('type')}'")
        v.check("bike" not in scenic_osm.get("supported_transports", []),
                "MAP_SCENIC_OSM: scenic must not support bike")


def validate_internal_nodes(nodes, maps, v: Validator):
    print("\n--- Internal Nodes ---")
    map_ids = {m.get("map_id") or m.get("id") for m in maps}

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
        # Simulated templates: require >= 20 entity nodes
        # Real maps: require >= 20 total nodes and >= 10 entity nodes
        if mid in REAL_MAP_IDS:
            v.check(len(map_nodes) >= 20,
                    f"{mid}: total nodes {len(map_nodes)} < 20 required")
            v.check(len(entities) >= 10,
                    f"{mid}: entity nodes {len(entities)} < 10 required")
            print(f"  {mid}: total={len(map_nodes)}, entities={len(entities)} "
                  f"{'OK' if len(map_nodes) >= 20 and len(entities) >= 10 else 'FAIL'}")
        else:
            v.check(len(entities) >= 20,
                    f"{mid}: entity nodes {len(entities)} < 20 required")
            print(f"  {mid}: total={len(map_nodes)}, entities={len(entities)} "
                  f"{'OK' if len(entities) >= 20 else 'FAIL'}")


def validate_internal_edges(edges, nodes, maps, v: Validator):
    print("\n--- Internal Edges ---")
    map_ids = {m.get("map_id") or m.get("id") for m in maps}
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
            if (m.get("map_id") or m.get("id")) == e["map_id"]:
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
    map_ids = {m.get("map_id") or m.get("id") for m in maps}
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

    # 1. 至少 2 个建筑
    v.check(len(indoor_maps) >= 2,
            f"indoor_maps count {len(indoor_maps)} < 2 required")
    print(f"  Indoor buildings: {len(indoor_maps)} {'OK' if len(indoor_maps) >= 2 else 'FAIL'}")

    # 2-3. 必须包含 campus_building 和 scenic_exhibition
    btypes = {b.get("building_type") for b in indoor_maps}
    v.check("campus_building" in btypes,
            "must have at least one campus_building")
    v.check("scenic_exhibition" in btypes,
            "must have at least one scenic_exhibition")
    print(f"  Building types: {btypes}")

    for bld in indoor_maps:
        bid = bld.get("building_id", "?")
        nodes = bld.get("nodes", [])
        edges = bld.get("edges", [])
        node_ids = {n["id"] for n in nodes}
        btype = bld.get("building_type", "")

        # 4. 必要字段
        for field in ["building_id", "building_name", "building_type",
                       "floors", "nodes", "edges"]:
            v.check(field in bld, f"{bid}: missing '{field}' field")
        v.check(len(bld.get("floors", [])) >= 2,
                f"{bid}: must have >= 2 floors")

        # 5. Node 字段
        for n in nodes:
            for field in ["id", "name", "floor", "type", "x", "y"]:
                v.check(field in n, f"{bid}/{n.get('id','?')}: missing node field '{field}'")

        # 6. Edge 字段
        for e in edges:
            for field in ["id", "from", "to", "distance", "type"]:
                v.check(field in e, f"{bid}/{e.get('id','?')}: missing edge field '{field}'")

        # 7. Edge 引用
        for e in edges:
            v.check(e["from"] in node_ids,
                    f"{bid}: edge '{e['id']}' from '{e['from']}' not found")
            v.check(e["to"] in node_ids,
                    f"{bid}: edge '{e['id']}' to '{e['to']}' not found")

        # 8. distance > 0
        for e in edges:
            v.check(e.get("distance", 0) > 0,
                    f"{bid}: edge '{e['id']}' distance must be > 0")

        # 9. 连通性
        is_connected, total, unreachable = check_connectivity(bid, nodes, edges)
        v.check(is_connected,
                f"{bid}: indoor graph not fully connected ({unreachable}/{total} unreachable)")

        # 10-11. 规模要求
        if btype == "campus_building":
            v.check(len(nodes) >= 35,
                    f"{bid}: campus_building nodes {len(nodes)} < 35 required")
            v.check(len(edges) >= 45,
                    f"{bid}: campus_building edges {len(edges)} < 45 required")
        elif btype == "scenic_exhibition":
            v.check(len(nodes) >= 25,
                    f"{bid}: scenic_exhibition nodes {len(nodes)} < 25 required")
            v.check(len(edges) >= 30,
                    f"{bid}: scenic_exhibition edges {len(edges)} < 30 required")

        # 12. 电梯跨层边
        has_elevator_edge = any(e.get("type") == "elevator" for e in edges)
        v.check(has_elevator_edge, f"{bid}: must have elevator cross-floor edges")

        # 13. 楼梯跨层边
        has_stairs_edge = any(e.get("type") == "stairs" for e in edges)
        v.check(has_stairs_edge, f"{bid}: must have stairs cross-floor edges")

        # 14. entrance
        has_entrance = any(n.get("type") == "entrance" for n in nodes)
        v.check(has_entrance, f"{bid}: must have entrance node")

        # 15. restroom
        has_restroom = any(n.get("type") == "restroom" for n in nodes)
        v.check(has_restroom, f"{bid}: must have restroom node")

        # 16. 目标节点 (classroom/office/exhibition_hall)
        has_target = any(n.get("type") in ("classroom", "office", "exhibition_hall") for n in nodes)
        v.check(has_target, f"{bid}: must have classroom/office/exhibition_hall nodes")

        # 汇总
        ntype_summary = Counter(n.get("type", "") for n in nodes)
        etype_summary = Counter(e.get("type", "") for e in edges)
        con_str = "connected" if is_connected else "DISCONNECTED"
        print(f"  {bid}: type={btype}, floors={bld.get('floors')}, "
              f"nodes={len(nodes)}, edges={len(edges)}, connectivity={con_str}")
        print(f"    Node types: {dict(ntype_summary)}")
        print(f"    Edge types: {dict(etype_summary)}")


def validate_coordinate_bounds(nodes, facilities, maps, v: Validator):
    """校验真实地图坐标范围，抽象模板不要求真实经纬度。"""
    print("\n--- Coordinate Bounds ---")

    REF_BUPT = {"lat": (39.9490, 39.9730), "lng": (116.3430, 116.3700)}
    REF_BNU = {"lat": (39.9560, 39.9700), "lng": (116.3590, 116.3730)}
    REF_SCENIC = {"lat": (39.8590, 39.9080), "lng": (116.3790, 116.4390)}
    REF_CAMPUS_OSM = {"lat": (39.9880, 40.0120), "lng": (116.3080, 116.3420)}
    REF_SCENIC_OSM = {"lat": (39.9860, 40.0100), "lng": (116.2580, 116.2870)}

    nodes_by_map = defaultdict(list)
    for n in nodes:
        nodes_by_map[n["map_id"]].append(n)

    facs_by_map = defaultdict(list)
    for f in facilities:
        facs_by_map[f["map_id"]].append(f)

    # MAP_BUPT_REAL coordinate check
    bupt_nodes = nodes_by_map.get("MAP_BUPT_REAL", [])
    if bupt_nodes:
        lats = [n["latitude"] for n in bupt_nodes]
        lngs = [n["longitude"] for n in bupt_nodes]
        for n in bupt_nodes:
            lat_ok = REF_BUPT["lat"][0] <= n["latitude"] <= REF_BUPT["lat"][1]
            lng_ok = REF_BUPT["lng"][0] <= n["longitude"] <= REF_BUPT["lng"][1]
            v.check(lat_ok and lng_ok,
                    f"{n['id']}: BUPT node ({n['latitude']:.4f}, {n['longitude']:.4f}) outside expected range")

        v.check(min(lats) >= REF_BUPT["lat"][0],
                f"BUPT min_lat {min(lats):.4f} < expected {REF_BUPT['lat'][0]}")
        v.check(max(lats) <= REF_BUPT["lat"][1],
                f"BUPT max_lat {max(lats):.4f} > expected {REF_BUPT['lat'][1]}")
        v.check(min(lngs) >= REF_BUPT["lng"][0],
                f"BUPT min_lng {min(lngs):.4f} < expected {REF_BUPT['lng'][0]}")
        v.check(max(lngs) <= REF_BUPT["lng"][1],
                f"BUPT max_lng {max(lngs):.4f} > expected {REF_BUPT['lng'][1]}")
        print(f"  MAP_BUPT_REAL: lat [{min(lats):.4f}, {max(lats):.4f}], lng [{min(lngs):.4f}, {max(lngs):.4f}]")

    # MAP_SCENIC_REAL coordinate check
    scenic_nodes = nodes_by_map.get("MAP_SCENIC_REAL", [])
    if scenic_nodes:
        lats = [n["latitude"] for n in scenic_nodes]
        lngs = [n["longitude"] for n in scenic_nodes]
        for n in scenic_nodes:
            lat_ok = REF_SCENIC["lat"][0] <= n["latitude"] <= REF_SCENIC["lat"][1]
            lng_ok = REF_SCENIC["lng"][0] <= n["longitude"] <= REF_SCENIC["lng"][1]
            v.check(lat_ok and lng_ok,
                    f"{n['id']}: SCENIC node ({n['latitude']:.4f}, {n['longitude']:.4f}) outside expected range")
        print(f"  MAP_SCENIC_REAL: lat [{min(lats):.4f}, {max(lats):.4f}], lng [{min(lngs):.4f}, {max(lngs):.4f}]")

    # MAP_BNU_REAL coordinate check
    bnu_nodes = nodes_by_map.get("MAP_BNU_REAL", [])
    if bnu_nodes:
        lats = [n["latitude"] for n in bnu_nodes]
        lngs = [n["longitude"] for n in bnu_nodes]
        v.check(min(lats) >= REF_BNU["lat"][0] and max(lats) <= REF_BNU["lat"][1],
                f"BNU lat range [{min(lats):.4f}, {max(lats):.4f}] outside expected")
        v.check(min(lngs) >= REF_BNU["lng"][0] and max(lngs) <= REF_BNU["lng"][1],
                f"BNU lng range [{min(lngs):.4f}, {max(lngs):.4f}] outside expected")
        print(f"  MAP_BNU_REAL: lat [{min(lats):.4f}, {max(lats):.4f}], lng [{min(lngs):.4f}, {max(lngs):.4f}]")

    # MAP_CAMPUS_OSM coordinate check (Tsinghua)
    campus_osm_nodes = nodes_by_map.get("MAP_CAMPUS_OSM", [])
    if campus_osm_nodes:
        lats = [n["latitude"] for n in campus_osm_nodes]
        lngs = [n["longitude"] for n in campus_osm_nodes]
        v.check(min(lats) >= REF_CAMPUS_OSM["lat"][0] and max(lats) <= REF_CAMPUS_OSM["lat"][1],
                f"MAP_CAMPUS_OSM lat range [{min(lats):.4f}, {max(lats):.4f}] outside expected")
        v.check(min(lngs) >= REF_CAMPUS_OSM["lng"][0] and max(lngs) <= REF_CAMPUS_OSM["lng"][1],
                f"MAP_CAMPUS_OSM lng range [{min(lngs):.4f}, {max(lngs):.4f}] outside expected")
        print(f"  MAP_CAMPUS_OSM: lat [{min(lats):.4f}, {max(lats):.4f}], lng [{min(lngs):.4f}, {max(lngs):.4f}]")

    # MAP_SCENIC_OSM coordinate check (Summer Palace)
    scenic_osm_nodes = nodes_by_map.get("MAP_SCENIC_OSM", [])
    if scenic_osm_nodes:
        lats = [n["latitude"] for n in scenic_osm_nodes]
        lngs = [n["longitude"] for n in scenic_osm_nodes]
        v.check(min(lats) >= REF_SCENIC_OSM["lat"][0] and max(lats) <= REF_SCENIC_OSM["lat"][1],
                f"MAP_SCENIC_OSM lat range [{min(lats):.4f}, {max(lats):.4f}] outside expected")
        v.check(min(lngs) >= REF_SCENIC_OSM["lng"][0] and max(lngs) <= REF_SCENIC_OSM["lng"][1],
                f"MAP_SCENIC_OSM lng range [{min(lngs):.4f}, {max(lngs):.4f}] outside expected")
        print(f"  MAP_SCENIC_OSM: lat [{min(lats):.4f}, {max(lats):.4f}], lng [{min(lngs):.4f}, {max(lngs):.4f}]")

    # Abstract templates: just check no facilities at (0,0)
    for mid in REQUIRED_MAP_IDS:
        mfacs = facs_by_map.get(mid, [])
        zero_facs = [f for f in mfacs if abs(f.get("latitude", 0)) < 0.001 and abs(f.get("longitude", 0)) < 0.001]
        v.check(len(zero_facs) == 0,
                f"{mid}: {len(zero_facs)} facilities still at (0,0)")
        mnodes = nodes_by_map.get(mid, [])
        zero_nodes = [n for n in mnodes if abs(n.get("latitude", 0)) < 0.001 and abs(n.get("longitude", 0)) < 0.001]
        v.check(len(zero_nodes) == 0,
                f"{mid}: {len(zero_nodes)} nodes still at (0,0)")
        # Validate center is not [0,0]
        map_obj = next((m for m in maps if (m.get("map_id") or m.get("id")) == mid), None)
        if map_obj:
            center = map_obj.get("center", [0, 0])
            v.check(center[0] != 0 or center[1] != 0,
                    f"{mid}: center is [0,0], should reflect node coordinates")
        print(f"  {mid}: no (0,0) facilities/nodes, center OK")

    # All maps: facilities should have valid coordinates
    for f in facilities:
        v.check(abs(f.get("latitude", 0)) > 0.001 or abs(f.get("longitude", 0)) > 0.001,
                f"{f['id']}: facility has (0,0) coordinate")


def validate_osm_vector_quality(nodes_list, edges_list, maps, v: Validator):
    """对 source=openstreetmap_vector 的地图进行质量校验。"""
    print("\n--- OSM Vector Quality ---")
    nodes_by_map = defaultdict(list)
    for n in nodes_list:
        nodes_by_map[n["map_id"]].append(n)
    edges_by_map = defaultdict(list)
    for e in edges_list:
        edges_by_map[e["map_id"]].append(e)

    for m in maps:
        mid = m.get("map_id") or m.get("id")
        source = m.get("source", "")

        if source == "openstreetmap_vector":
            map_edges = edges_by_map.get(mid, [])
            map_nodes = nodes_by_map.get(mid, [])

            # 每条边必须有 geometry
            for e in map_edges:
                geom = e.get("geometry")
                v.check(geom is not None and len(geom) >= 2,
                        f"{e['id']}: openstreetmap_vector edge must have geometry with >= 2 points")
                if geom:
                    # geometry 坐标在 bbox 内
                    for pt in geom:
                        v.check(abs(pt[0]) > 0.001 and abs(pt[1]) > 0.001,
                                f"{e['id']}: geometry point {pt} near (0,0)")

            # 数量要求
            v.check(len(map_edges) >= 60,
                    f"{mid}: openstreetmap_vector edges {len(map_edges)} < 60 required")
            v.check(len(map_nodes) >= 20,
                    f"{mid}: openstreetmap_vector nodes {len(map_nodes)} < 20 required")

            print(f"  {mid}: nodes={len(map_nodes)}, edges={len(map_edges)} — OK")

        elif source == "manual_osm_aligned":
            v.check(m.get("show_tile") is True,
                    f"{mid}: manual_osm_aligned must have show_tile=true")
            v.check(m.get("semi_real_map") is True,
                    f"{mid}: manual_osm_aligned must have semi_real_map=true")
            map_edges = edges_by_map.get(mid, [])
            for e in map_edges:
                v.check(e.get("geometry") is not None,
                        f"{e['id']}: manual_osm_aligned edge must have geometry")
            print(f"  {mid}: manual_osm_aligned — OK")

        elif source == "openstreetmap":
            # 旧的 misleading source
            map_edges = edges_by_map.get(mid, [])
            edges_with_geom = sum(1 for e in map_edges if e.get("geometry"))
            v.check(edges_with_geom > 0,
                    f"{mid}: source='openstreetmap' but no edges have geometry — source misleading, update to openstreetmap_vector or manual_osm_aligned")
            print(f"  {mid}: legacy 'openstreetmap' source — WARNING")

    # 交通约束
    for m in maps:
        mid = m.get("map_id") or m.get("id")
        map_type = m.get("type")
        map_edges = edges_by_map.get(mid, [])
        if map_type == "campus":
            for e in map_edges:
                v.check("sightseeing_car" not in e.get("allowed_transport", []),
                        f"{e['id']}: campus map edge must not have sightseeing_car")
        elif map_type == "attraction":
            for e in map_edges:
                v.check("bike" not in e.get("allowed_transport", []),
                        f"{e['id']}: attraction map edge must not have bike")


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
    validate_coordinate_bounds(nodes, facilities, maps, v)
    validate_osm_vector_quality(nodes, edges, maps, v)
    validate_users(users, v)
    validate_indoor_graphs(indoor_data, v)
    validate_connectivity(nodes, edges, v)

    # Report
    failed = v.report()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
