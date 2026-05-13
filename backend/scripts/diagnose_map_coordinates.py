"""
Diagnose map coordinates — 分析每个 internal_map_id 的坐标范围和健康度。
"""
import json
import sys
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# 参考范围
REF_BUPT = {"lat_min": 39.952, "lat_max": 39.970, "lng_min": 116.347, "lng_max": 116.366}
REF_SCENIC = {"lat_min": 39.864, "lat_max": 39.903, "lng_min": 116.385, "lng_max": 116.433}

def load_json(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)

def lat_lng_dist(lat1, lng1, lat2, lng2):
    """粗略纬度距离估计 (km)"""
    dlat = (lat2 - lat1) * 111.32
    dlng = (lng2 - lng1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.sqrt(dlat**2 + dlng**2)

def check_bounds(lats, lngs, ref, map_name):
    """检查坐标是否在参考范围内"""
    warnings = []
    out_of_range = 0
    total = len(lats)
    for i in range(total):
        lat_ok = ref["lat_min"] <= lats[i] <= ref["lat_max"]
        lng_ok = ref["lng_min"] <= lngs[i] <= ref["lng_max"]
        if not lat_ok or not lng_ok:
            out_of_range += 1
    if out_of_range > total * 0.3:
        warnings.append(f"  ⚠️ WARNING: {out_of_range}/{total} 节点超出参考范围")
    elif out_of_range > 0:
        warnings.append(f"  ⚡ {out_of_range}/{total} 节点超出参考范围（少量）")
    return warnings

def main():
    destinations = load_json("destinations.json")
    maps = load_json("internal_maps.json")
    nodes = load_json("internal_nodes.json")
    edges = load_json("internal_edges.json")
    facilities = load_json("facilities.json")

    # 索引
    dest_by_id = {d["id"]: d for d in destinations}
    map_by_id = {m["map_id"]: m for m in maps}
    nodes_by_map = {}
    edges_by_map = {}
    facs_by_map = {}

    for n in nodes:
        mid = n.get("map_id", "")
        nodes_by_map.setdefault(mid, []).append(n)
    for e in edges:
        mid = e.get("map_id", "")
        edges_by_map.setdefault(mid, []).append(e)
    for f in facilities:
        mid = f.get("map_id", "")
        facs_by_map.setdefault(mid, []).append(f)

    lines = []
    def p(s=""):
        lines.append(s)
        print(s)

    p("# 地图坐标诊断报告")
    p()
    p(f"生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    p()

    all_warnings = []

    for m in maps:
        mid = m["map_id"]
        mnodes = nodes_by_map.get(mid, [])
        medges = edges_by_map.get(mid, [])
        mfacs = facs_by_map.get(mid, [])

        lats = [n["latitude"] for n in mnodes]
        lngs = [n["longitude"] for n in mnodes]
        valid_lats = [x for x in lats if abs(x) > 0.001]
        valid_lngs = [x for x in lngs if abs(x) > 0.001]

        p(f"## {mid} — {m['name']}")
        p()
        p(f"- type: {m['type']}")
        p(f"- is_real_map: {m['is_real_map']}")
        p(f"- show_tile: {m['show_tile']}")
        p(f"- center: {m['center']}")
        p(f"- node_count: {len(mnodes)}")
        p(f"- edge_count: {len(medges)}")
        p(f"- facility_count: {len(mfacs)}")

        if valid_lats:
            p(f"- min_lat: {min(valid_lats):.6f}, max_lat: {max(valid_lats):.6f}")
            p(f"- min_lng: {min(valid_lngs):.6f}, max_lng: {max(valid_lngs):.6f}")
            avg_lat = sum(valid_lats) / len(valid_lats)
            avg_lng = sum(valid_lngs) / len(valid_lngs)
            p(f"- 节点中心点平均坐标: [{avg_lat:.6f}, {avg_lng:.6f}]")

            center_lat, center_lng = m["center"]
            if abs(center_lat) > 0.001 and abs(center_lng) > 0.001:
                dist = lat_lng_dist(center_lat, center_lng, avg_lat, avg_lng)
                p(f"- center 与节点平均坐标距离估计: {dist:.3f} km")
        else:
            p("- min_lat: N/A (no valid coordinates)")
            p("- min_lng: N/A (no valid coordinates)")

        # 前 10 个节点
        p()
        p("### 前 10 个节点")
        p()
        for n in mnodes[:10]:
            p(f"  - {n['id']}: ({n['latitude']:.6f}, {n['longitude']:.6f}) {n['name']}")

        # 前 10 个设施
        if mfacs:
            p()
            p("### 前 10 个设施")
            p()
            for f in mfacs[:10]:
                p(f"  - {f['id']}: ({f['latitude']:.6f}, {f['longitude']:.6f}) {f['name']} (linked: {f['linked_node_id']})")

        # 检查真实地图坐标范围
        if m["is_real_map"]:
            p()
            if mid == "MAP_BUPT_REAL":
                p("### BUPT 坐标参考范围检查")
                p(f"- 参考范围: lat [{REF_BUPT['lat_min']}, {REF_BUPT['lat_max']}], lng [{REF_BUPT['lng_min']}, {REF_BUPT['lng_max']}]")
                warnings = check_bounds(valid_lats, valid_lngs, REF_BUPT, m['name'])
                for w in warnings:
                    p(w)
                    all_warnings.append((mid, w))
            elif mid == "MAP_SCENIC_REAL":
                p("### SCENIC 坐标参考范围检查")
                p(f"- 参考范围: lat [{REF_SCENIC['lat_min']}, {REF_SCENIC['lat_max']}], lng [{REF_SCENIC['lng_min']}, {REF_SCENIC['lng_max']}]")
                warnings = check_bounds(valid_lats, valid_lngs, REF_SCENIC, m['name'])
                for w in warnings:
                    p(w)
                    all_warnings.append((mid, w))

        # 设施坐标检查
        if mfacs:
            fac_zero = sum(1 for f in mfacs if abs(f["latitude"]) < 0.001 and abs(f["longitude"]) < 0.001)
            if fac_zero > 0:
                w = f"  ⚠️ WARNING: {fac_zero}/{len(mfacs)} 设施坐标为 (0, 0) — 无法在前端渲染"
                p(w)
                all_warnings.append((mid, w))

        # 边连通性快速检查
        node_ids = {n["id"] for n in mnodes}
        edge_refs = set()
        for e in medges:
            edge_refs.add(e["from"])
            edge_refs.add(e["to"])
        orphan = edge_refs - node_ids
        if orphan:
            w = f"  ⚠️ WARNING: {len(orphan)} 条边引用了不存在的节点"
            p(w)
            all_warnings.append((mid, w))

        p()
        p("---")
        p()

    # 目的地绑定检查
    p("## 目的地绑定检查")
    p()
    real_bound = {"MAP_BUPT_REAL": [], "MAP_SCENIC_REAL": []}
    for d in destinations:
        mid = d.get("internal_map_id", "")
        if mid in real_bound:
            real_bound[mid].append(d["id"])

    p(f"- MAP_BUPT_REAL 绑定目的地: {len(real_bound['MAP_BUPT_REAL'])}: {real_bound['MAP_BUPT_REAL']}")
    p(f"- MAP_SCENIC_REAL 绑定目的地: {len(real_bound['MAP_SCENIC_REAL'])}: {real_bound['MAP_SCENIC_REAL']}")

    # 检查 DEST_001 绑定
    d001 = dest_by_id.get("DEST_001")
    if d001:
        p(f"- DEST_001 (北京邮电大学) → {d001.get('internal_map_id')}")
        if d001.get("internal_map_id") != "MAP_BUPT_REAL":
            w = "⚠️ WARNING: DEST_001 未绑定 MAP_BUPT_REAL!"
            p(w)
            all_warnings.append(("DEST_001", w))

    d032 = dest_by_id.get("DEST_032")
    if d032:
        p(f"- DEST_032 (天坛公园) → {d032.get('internal_map_id')}")
        if d032.get("internal_map_id") != "MAP_SCENIC_REAL":
            w = "⚠️ WARNING: DEST_032 未绑定 MAP_SCENIC_REAL!"
            p(w)
            all_warnings.append(("DEST_032", w))

    # 抽象模板坐标检查
    p()
    p("## 抽象模板坐标自洽性")
    p()
    for mid in ["MAP_CAMPUS_001", "MAP_SCENIC_001", "MAP_MIXED_001"]:
        m = map_by_id.get(mid)
        if not m:
            continue
        mnodes = nodes_by_map.get(mid, [])
        valid_lats = [n["latitude"] for n in mnodes if abs(n["latitude"]) > 0.001]
        valid_lngs = [n["longitude"] for n in mnodes if abs(n["longitude"]) > 0.001]
        invalid = len(mnodes) - len(valid_lats)

        node_ids = {n["id"] for n in mnodes}
        mfacs = facs_by_map.get(mid, [])
        mfacs_zero = sum(1 for f in mfacs if abs(f["latitude"]) < 0.001)
        mfacs_with_linked = 0
        mfacs_with_valid_coord = 0
        for f in mfacs:
            if f["linked_node_id"] in node_ids:
                mfacs_with_linked += 1
                linked_node = next((n for n in mnodes if n["id"] == f["linked_node_id"]), None)
                if linked_node and abs(linked_node["latitude"]) > 0.001:
                    mfacs_with_valid_coord += 1

        p(f"- {mid} ({m['name']}):")
        p(f"  - 总节点: {len(mnodes)}, 有效坐标: {len(valid_lats)}, 无效坐标: {invalid}")
        if valid_lats:
            p(f"  - lat 范围: [{min(valid_lats):.6f}, {max(valid_lats):.6f}]")
            p(f"  - lng 范围: [{min(valid_lngs):.6f}, {max(valid_lngs):.6f}]")
        p(f"  - 总设施: {len(mfacs)}, 坐标为(0,0): {mfacs_zero}, linked_node 有效坐标: {mfacs_with_valid_coord}")
        p(f"  - center: {m['center']}")

        if mfacs_zero > 0:
            w = f"⚠️ {mid} 有 {mfacs_zero} 个设施坐标为 (0,0)，需要修复"
            p(f"  - {w}")
            all_warnings.append((mid, w))

    # 总结
    p()
    p("## 总结")
    p()
    if all_warnings:
        p("发现以下问题：")
        for mid, w in all_warnings:
            p(f"  - [{mid}] {w}")
    else:
        p("✅ 所有地图坐标数据健康。")

    # 写入文件
    output = PROJECT_ROOT / "docs" / "map_coordinate_diagnosis.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告已写入：{output}")

    return 0 if not all_warnings else 1


if __name__ == "__main__":
    sys.exit(main())
