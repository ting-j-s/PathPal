"""
内部地图 API 路由
提供 internal_maps 查询（元数据含 is_real_map / show_tile / center）
以及 destination 地图图层数据。
"""
from flask import Blueprint, request, jsonify
from backend.services.data_loader import (
    load_internal_maps,
    load_internal_nodes,
    load_internal_edges,
    load_facilities,
    get_destination_by_id,
    get_internal_map_for_destination,
    get_map_id_by_destination_id,
    _invalidate_cache,
)


map_bp = Blueprint("map", __name__, url_prefix="/api")


@map_bp.route("/internal-maps", methods=["GET"])
def list_internal_maps():
    maps = load_internal_maps()
    result = []
    for m in maps:
        result.append({
            "map_id": m.get("map_id"),
            "name": m.get("name"),
            "type": m.get("type"),
            "description": m.get("description"),
            "source": m.get("source"),
            "is_real_map": m.get("is_real_map", False),
            "show_tile": m.get("show_tile", False),
            "center": m.get("center"),
            "default_zoom": m.get("default_zoom"),
            "supported_transports": m.get("supported_transports", []),
            "tile_note": m.get("tile_note"),
        })
    return jsonify({
        "count": len(result),
        "maps": result,
    })


@map_bp.route("/internal-maps/<map_id>", methods=["GET"])
def get_internal_map(map_id):
    maps = load_internal_maps()
    for m in maps:
        if m.get("map_id") == map_id:
            return jsonify({
                "map_id": m.get("map_id"),
                "name": m.get("name"),
                "type": m.get("type"),
                "description": m.get("description"),
                "source": m.get("source"),
                "is_real_map": m.get("is_real_map", False),
                "show_tile": m.get("show_tile", False),
                "center": m.get("center"),
                "default_zoom": m.get("default_zoom"),
                "supported_transports": m.get("supported_transports", []),
                "tile_note": m.get("tile_note"),
            })
    return jsonify({"error": f"Map not found: {map_id}", "type": "ValueError"}), 404


@map_bp.route("/destinations/<destination_id>/map-layers", methods=["GET"])
def get_destination_map_layers(destination_id):
    """返回 destination 对应的内部地图的完整图层数据（节点+边+设施）。"""
    _invalidate_cache()
    try:
        dest = get_destination_by_id(destination_id)
        map_id = dest["internal_map_id"]
        internal_map = get_internal_map_for_destination(destination_id)
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400

    all_nodes = load_internal_nodes()
    all_edges = load_internal_edges()
    all_facilities = load_facilities()

    nodes = [n for n in all_nodes if n.get("map_id") == map_id]
    edges = [e for e in all_edges if e.get("map_id") == map_id]
    facilities = [f for f in all_facilities if f.get("map_id") == map_id]

    # 精简节点输出
    nodes_out = []
    for n in nodes:
        nodes_out.append({
            "id": n["id"],
            "name": n.get("name", ""),
            "type": n.get("type", ""),
            "subtype": n.get("subtype", ""),
            "latitude": n.get("latitude", 0),
            "longitude": n.get("longitude", 0),
        })

    # 精简边输出
    edges_out = []
    for e in edges:
        edges_out.append({
            "id": e["id"],
            "from": e["from"],
            "to": e["to"],
            "distance": e.get("distance", 0),
            "allowed_transport": e.get("allowed_transport", []),
            "road_type": e.get("road_type", ""),
            "congestion": e.get("congestion", 1.0),
            "geometry": e.get("geometry", []),
        })

    # 精简设施输出（含 linked_node_id, lat/lng）
    facilities_out = []
    for f in facilities:
        facilities_out.append({
            "id": f["id"],
            "name": f.get("name", ""),
            "category": f.get("category", ""),
            "linked_node_id": f.get("linked_node_id", ""),
            "latitude": f.get("latitude", 0),
            "longitude": f.get("longitude", 0),
            "description": f.get("description", ""),
        })

    return jsonify({
        "destination_id": destination_id,
        "map_id": map_id,
        "internal_map": {
            "map_id": internal_map.get("map_id"),
            "name": internal_map.get("name"),
            "type": internal_map.get("type"),
            "is_real_map": internal_map.get("is_real_map", False),
            "show_tile": internal_map.get("show_tile", False),
            "center": internal_map.get("center"),
            "default_zoom": internal_map.get("default_zoom"),
            "supported_transports": internal_map.get("supported_transports", []),
            "tile_note": internal_map.get("tile_note", ""),
        },
        "nodes": nodes_out,
        "edges": edges_out,
        "facilities": facilities_out,
    })
