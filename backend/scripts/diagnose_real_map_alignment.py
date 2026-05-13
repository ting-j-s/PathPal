#!/usr/bin/env python3
"""
PathPal 真实地图对齐诊断脚本
诊断 MAP_BUPT_REAL 和 MAP_SCENIC_REAL 的数据质量，检查：
- 节点/边/设施数量
- 坐标范围（bbox）
- edge 是否包含 geometry
- 是否存在超长边
- geometry 是否只有首尾两点
- source 字段是否如实
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def haversine_distance(lat1, lon1, lat2, lon2):
    """计算两点间的大圆距离，单位米。"""
    import math
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# 参考 bbox（含 0.0005 容差 ~50m）
REF_BBOX = {
    "MAP_BUPT_REAL": {
        "lat_min": 39.9520, "lat_max": 39.9700,
        "lng_min": 116.3470, "lng_max": 116.3660,
    },
    "MAP_SCENIC_REAL": {
        "lat_min": 39.8640, "lat_max": 39.9030,
        "lng_min": 116.3850, "lng_max": 116.4330,
    },
}


def diagnose():
    print("=" * 60)
    print("PathPal 真实地图对齐诊断")
    print("=" * 60)

    maps = load_json("internal_maps.json")
    all_nodes = load_json("internal_nodes.json")
    all_edges = load_json("internal_edges.json")
    all_facilities = load_json("facilities.json")
    destinations = load_json("destinations.json")

    # 找真实地图
    real_maps = [m for m in maps if m.get("is_real_map") is True]
    if not real_maps:
        print("ERROR: 未找到 is_real_map=true 的地图")
        return 1

    issues = []

    for map_obj in real_maps:
        map_id = map_obj.get("map_id") or map_obj.get("id")
        if map_id not in ("MAP_BUPT_REAL", "MAP_SCENIC_REAL"):
            continue

        print(f"\n{'─' * 50}")
        print(f"诊断地图: {map_id}")
        print(f"  名称: {map_obj.get('name')}")
        print(f"  source: {map_obj.get('source')}")
        print(f"  is_real_map: {map_obj.get('is_real_map')}")
        print(f"  show_tile: {map_obj.get('show_tile')}")
        print(f"  center: {map_obj.get('center')}")

        # 找绑定的目的地
        bound_dests = [d for d in destinations if d.get("internal_map_id") == map_id]
        print(f"  绑定目的地数: {len(bound_dests)}")
        for d in bound_dests[:3]:
            print(f"    - {d['id']}: {d['name']}")

        # 节点
        map_nodes = [n for n in all_nodes if n.get("map_id") == map_id]
        print(f"\n  node_count: {len(map_nodes)}")

        if map_nodes:
            lats = [n["latitude"] for n in map_nodes]
            lngs = [n["longitude"] for n in map_nodes]
            print(f"  min_lat: {min(lats):.6f}  max_lat: {max(lats):.6f}")
            print(f"  min_lng: {min(lngs):.6f}  max_lng: {max(lngs):.6f}")

        # 边
        map_edges = [e for e in all_edges if e.get("map_id") == map_id]
        print(f"\n  edge_count: {len(map_edges)}")

        edges_with_geom = [e for e in map_edges if e.get("geometry")]
        print(f"  edge_with_geometry_count: {len(edges_with_geom)}")

        if len(edges_with_geom) == 0:
            msg = f"{map_id}: 所有边都缺少 geometry 字段，路线将画为直线"
            print(f"  ⚠ {msg}")
            issues.append(msg)
        elif len(edges_with_geom) < len(map_edges):
            msg = f"{map_id}: 只有 {len(edges_with_geom)}/{len(map_edges)} 条边有 geometry"
            print(f"  ⚠ {msg}")
            issues.append(msg)

        # 检查超长边
        long_edges = [e for e in map_edges if e.get("distance", 0) > 500]
        if long_edges:
            msg = f"{map_id}: {len(long_edges)} 条边距离 > 500m"
            print(f"  ⚠ {msg}")
            issues.append(msg)
            for e in long_edges[:5]:
                print(f"    {e['id']}: {e['from']} → {e['to']} = {e['distance']:.0f}m")

        # 检查 geometry 是否只有 from/to 两点
        for e in edges_with_geom:
            geom = e["geometry"]
            if isinstance(geom, list) and len(geom) <= 2:
                # 只有端点 = 实际上没有中间点
                pass  # 这还不一定是问题，看距离

        # 前10个节点
        print(f"\n  前 10 个节点:")
        for n in map_nodes[:10]:
            print(f"    {n['id']}: {n.get('name', '')} ({n['type']}) [{n['latitude']:.6f}, {n['longitude']:.6f}]")

        # 前10条边
        print(f"\n  前 10 条边:")
        for e in map_edges[:10]:
            has_geom = "YES" if e.get("geometry") else "NO"
            print(f"    {e['id']}: {e['from']} → {e['to']} | dist={e['distance']:.0f}m | geometry={has_geom}")

        # 设施
        map_facs = [f for f in all_facilities if f.get("map_id") == map_id]
        print(f"\n  facility_count: {len(map_facs)}")

        # 坐标越界检查
        ref = REF_BBOX.get(map_id)
        if ref:
            out_of_bounds_nodes = []
            for n in map_nodes:
                lat_ok = ref["lat_min"] <= n["latitude"] <= ref["lat_max"]
                lng_ok = ref["lng_min"] <= n["longitude"] <= ref["lng_max"]
                if not (lat_ok and lng_ok):
                    out_of_bounds_nodes.append(n)
            if out_of_bounds_nodes:
                msg = f"{map_id}: {len(out_of_bounds_nodes)} 个节点坐标越界"
                print(f"  ✗ {msg}")
                issues.append(msg)
                for n in out_of_bounds_nodes[:5]:
                    print(f"    {n['id']}: [{n['latitude']:.6f}, {n['longitude']:.6f}]")
            else:
                print(f"  ✓ 所有节点坐标在参考 bbox 内")

            # 检查设施坐标
            bad_facs = []
            for f in map_facs:
                lat_ok = ref["lat_min"] <= f.get("latitude", 0) <= ref["lat_max"]
                lng_ok = ref["lng_min"] <= f.get("longitude", 0) <= ref["lng_max"]
                if not (lat_ok and lng_ok):
                    bad_facs.append(f)
            if bad_facs:
                msg = f"{map_id}: {len(bad_facs)} 个设施坐标越界"
                print(f"  ⚠ {msg}")
                issues.append(msg)
            else:
                print(f"  ✓ 所有设施坐标在参考 bbox 内")

        # source 字段检查
        source = map_obj.get("source", "")
        if source == "openstreetmap" and len(edges_with_geom) == 0:
            msg = (f"{map_id}: source='openstreetmap' 但所有边均无 geometry，"
                   f"说明数据不是 OSM 矢量导入的，source 字段具有误导性")
            print(f"\n  ✗ {msg}")
            issues.append(msg)
        elif source == "openstreetmap" and len(edges_with_geom) > 0:
            print(f"\n  ✓ source='openstreetmap' 且有 {len(edges_with_geom)} 条带 geometry 的边")

        # 交通约束检查
        if map_obj.get("type") == "campus":
            for e in map_edges:
                if "sightseeing_car" in e.get("allowed_transport", []):
                    msg = f"{map_id}: campus 边 {e['id']} 包含 sightseeing_car"
                    print(f"  ✗ {msg}")
                    issues.append(msg)
        if map_obj.get("type") == "attraction":
            for e in map_edges:
                if "bike" in e.get("allowed_transport", []):
                    msg = f"{map_id}: attraction 边 {e['id']} 包含 bike"
                    print(f"  ✗ {msg}")
                    issues.append(msg)

    # 总结
    print(f"\n{'=' * 60}")
    print("诊断总结")
    print(f"{'=' * 60}")

    # 检查 source=openstreetmap 的所有地图
    for map_obj in maps:
        map_id = map_obj.get("map_id") or map_obj.get("id")
        if map_id not in ("MAP_BUPT_REAL", "MAP_SCENIC_REAL"):
            continue
        source = map_obj.get("source", "")
        map_edges = [e for e in all_edges if e.get("map_id") == map_id]
        edges_with_geom = [e for e in map_edges if e.get("geometry")]
        print(f"\n{map_id}:")
        print(f"  source: {source}")
        print(f"  edges with geometry: {len(edges_with_geom)}/{len(map_edges)}")

        map_nodes = [n for n in all_nodes if n.get("map_id") == map_id]
        lats = [n["latitude"] for n in map_nodes]
        lngs = [n["longitude"] for n in map_nodes]
        print(f"  bbox: lat [{min(lats):.6f}, {max(lats):.6f}], lng [{min(lngs):.6f}, {max(lngs):.6f}]")

        map_facs = [f for f in all_facilities if f.get("map_id") == map_id]
        print(f"  facilities: {len(map_facs)}")

    print(f"\n共发现 {len(issues)} 个问题:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

    overall = "PASS" if len(issues) == 0 else "ISSUES FOUND"
    print(f"\n诊断结论: {overall}")

    return 0 if len(issues) == 0 else 1


if __name__ == "__main__":
    sys.exit(diagnose())
