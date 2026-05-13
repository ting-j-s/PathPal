"""
PathPal 统一数据加载器
从 data/ 目录读取所有 JSON 文件，提供内存缓存和查询接口。
"""
import json
from pathlib import Path

from backend.algorithms.graph import load_graph_from_data

# 导入 config
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import config

DATA_DIR = config.DATA_DIR


def load_json(filepath):
    """读取单个 JSON 文件。"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 内存缓存
# ============================================================
_cache = {}


def _cached(key, loader_fn):
    """读一次后缓存。"""
    if key not in _cache:
        _cache[key] = loader_fn()
    return _cache[key]


def _invalidate_cache():
    """清空缓存（测试用）。"""
    _cache.clear()


# ============================================================
# 数据加载函数
# ============================================================
def load_destinations():
    return _cached("destinations", lambda: load_json(config.DESTINATIONS_FILE))


def load_internal_maps():
    return _cached("internal_maps", lambda: load_json(config.INTERNAL_MAPS_FILE))


def load_internal_nodes():
    return _cached("internal_nodes", lambda: load_json(config.INTERNAL_NODES_FILE))


def load_internal_edges():
    return _cached("internal_edges", lambda: load_json(config.INTERNAL_EDGES_FILE))


def load_facilities():
    return _cached("facilities", lambda: load_json(config.FACILITIES_FILE))


def load_users():
    return _cached("users", lambda: load_json(config.USERS_FILE))


def load_indoor_graphs():
    data = _cached("indoor_graphs", lambda: load_json(config.INDOOR_GRAPHS_FILE))
    if isinstance(data, dict) and "indoor_maps" in data:
        return data
    return {"indoor_maps": data} if isinstance(data, list) else data


# ============================================================
# 查询辅助函数
# ============================================================
def _find_by_id(items, item_id):
    for item in items:
        if item.get("id") == item_id:
            return item
    return None


def get_destination_by_id(destination_id):
    dest = _find_by_id(load_destinations(), destination_id)
    if dest is None:
        raise ValueError(f"Destination not found: {destination_id}")
    return dest


def get_user_by_id(user_id):
    user = _find_by_id(load_users(), user_id)
    if user is None:
        raise ValueError(f"User not found: {user_id}")
    return user


def get_map_id_by_destination_id(destination_id):
    dest = get_destination_by_id(destination_id)
    return dest["internal_map_id"]


def get_destination_type(destination_id):
    dest = get_destination_by_id(destination_id)
    return dest["type"]


def load_graph_for_destination(destination_id):
    """根据 destination_id 加载对应的内部道路图。"""
    map_id = get_map_id_by_destination_id(destination_id)
    nodes = load_internal_nodes()
    edges = load_internal_edges()
    return load_graph_from_data(nodes, edges, map_id)


def get_facilities_for_destination(destination_id):
    """返回该目的地内部地图下所有设施。"""
    map_id = get_map_id_by_destination_id(destination_id)
    facilities = load_facilities()
    return [f for f in facilities if f.get("map_id") == map_id]


def get_nodes_for_destination(destination_id):
    """返回该目的地内部地图下所有节点。"""
    map_id = get_map_id_by_destination_id(destination_id)
    nodes = load_internal_nodes()
    return [n for n in nodes if n.get("map_id") == map_id]


def get_destination_count():
    return len(load_destinations())


def get_map_count():
    return len(load_internal_maps())


def get_node_count():
    return len(load_internal_nodes())


def get_edge_count():
    return len(load_internal_edges())


def get_facility_count():
    return len(load_facilities())


def get_user_count():
    return len(load_users())


def get_stats():
    """返回数据统计信息。"""
    facilities = load_facilities()
    cats = set(f["category"] for f in facilities)
    indoor = load_indoor_graphs()
    indoor_maps = indoor.get("indoor_maps", [])
    return {
        "destinations": get_destination_count(),
        "internal_maps": get_map_count(),
        "internal_nodes": get_node_count(),
        "internal_edges": get_edge_count(),
        "facilities": get_facility_count(),
        "facility_categories": len(cats),
        "users": get_user_count(),
        "indoor_buildings": len(indoor_maps),
    }
