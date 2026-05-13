"""
PathPal 附近设施查询（道路距离排序）

核心原则：使用道路图最短路径距离进行排序，
不得使用经纬度直线距离作为最终排序依据。
"""
from .dijkstra import dijkstra_shortest_distance, extract_route_geometry
from .sorting import merge_sort, get_value
from .search import _match_value


def calculate_nearby_facilities_by_road_distance(
    graph,
    origin_node_id,
    facilities,
    radius=None,
    category=None,
    keyword=None,
):
    """
    基于道路距离计算附近设施。

    参数:
        graph: Graph 对象
        origin_node_id: 起点节点 ID
        facilities: 设施列表（应已限定在同一 map_id）
        radius: 道路距离上限（米），None 表示不限制
        category: 设施类别过滤，None 表示不过滤
        keyword: 关键词搜索，匹配 name/category/description

    返回:
        [{
            **facility 原始字段,
            "road_distance": float,
            "path": [node_id, ...],
            "coordinates": [lat, lng]
        }, ...]
        按 road_distance 升序排列。
    """
    results = []

    for facility in facilities:
        # 类别过滤
        if category is not None and facility.get("category") != category:
            continue

        # 关键词过滤
        if keyword is not None:
            kw_lower = str(keyword).lower()
            matched = False
            for field in ["name", "category", "description"]:
                if _match_value(facility.get(field), kw_lower):
                    matched = True
                    break
            if not matched:
                continue

        linked_node_id = facility.get("linked_node_id")
        if linked_node_id is None:
            continue

        # 确保 linked_node_id 在图中有对应节点
        if not graph.has_node(linked_node_id):
            continue

        # 计算道路最短路径距离
        route_result = dijkstra_shortest_distance(graph, origin_node_id, linked_node_id)
        if not route_result["reachable"]:
            continue

        road_distance = route_result["total_distance"]

        # 半径过滤
        if radius is not None and road_distance > radius:
            continue

        # 获取设施坐标
        coordinates = None
        fac_lat = facility.get("latitude")
        fac_lng = facility.get("longitude")
        if fac_lat is not None and fac_lng is not None:
            coordinates = [fac_lat, fac_lng]

        result_entry = dict(facility)
        result_entry["road_distance"] = road_distance
        result_entry["path"] = route_result["path"]
        result_entry["coordinates"] = coordinates
        result_entry["route_geometry"] = extract_route_geometry(route_result["segments"])
        result_entry["segments"] = route_result["segments"]
        results.append(result_entry)

    # 按 road_distance 升序排序（使用自己实现的排序）
    results = merge_sort(results, key="road_distance", reverse=False)

    return results


def validate_facilities_same_map(facilities, map_id):
    """确保所有设施都属于当前 map_id。"""
    for f in facilities:
        if f.get("map_id") != map_id:
            return False
    return True


def extract_path_coordinates(graph, path):
    """返回路径上每个节点的坐标列表 [[lat, lng], ...]。"""
    coords = []
    for node_id in path:
        coord = graph.get_coordinates(node_id)
        if coord is not None:
            coords.append(coord)
    return coords
