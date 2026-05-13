"""
PathPal 场所查询服务
封装景区/校园内部附近设施查询，基于道路距离排序。
"""
from backend.services import data_loader
from backend.algorithms.nearby import calculate_nearby_facilities_by_road_distance

NOTE_TEXT = "排序依据为道路网络最短路径距离，不是经纬度直线距离"


class NearbyService:

    def _make_result(self, destination_id, origin_node_id, facilities):
        """构建统一返回格式。"""
        dest = data_loader.get_destination_by_id(destination_id)
        return {
            "destination_id": destination_id,
            "destination_name": dest["name"],
            "internal_map_id": dest["internal_map_id"],
            "origin": origin_node_id,
            "algorithm": "Dijkstra + Road Distance Sorting (Merge Sort)",
            "data_structure": "Internal Graph Adjacency List",
            "note": NOTE_TEXT,
            "count": len(facilities),
            "facilities": facilities,
        }

    def find_nearby(self, destination_id, node_id, radius=None):
        """从 node_id 出发一定半径内所有设施，按道路距离排序。"""
        graph = data_loader.load_graph_for_destination(destination_id)
        facilities = data_loader.get_facilities_for_destination(destination_id)
        results = calculate_nearby_facilities_by_road_distance(
            graph, node_id, facilities, radius=radius,
        )
        return self._make_result(destination_id, node_id, results)

    def find_by_category(self, destination_id, node_id, category, radius=None):
        """按类别过滤附近设施。"""
        graph = data_loader.load_graph_for_destination(destination_id)
        facilities = data_loader.get_facilities_for_destination(destination_id)
        results = calculate_nearby_facilities_by_road_distance(
            graph, node_id, facilities, radius=radius, category=category,
        )
        return self._make_result(destination_id, node_id, results)

    def search_nearby(self, destination_id, node_id, keyword, radius=None):
        """按关键词搜索附近设施。"""
        graph = data_loader.load_graph_for_destination(destination_id)
        facilities = data_loader.get_facilities_for_destination(destination_id)
        results = calculate_nearby_facilities_by_road_distance(
            graph, node_id, facilities, radius=radius, keyword=keyword,
        )
        return self._make_result(destination_id, node_id, results)

    def list_facility_categories(self, destination_id=None):
        """返回设施类别列表。"""
        if destination_id:
            facilities = data_loader.get_facilities_for_destination(destination_id)
        else:
            facilities = data_loader.load_facilities()

        cats = sorted(set(f["category"] for f in facilities))
        return {
            "destination_id": destination_id,
            "count": len(cats),
            "categories": cats,
        }

    def list_facilities(self, destination_id):
        """返回某目的地内部地图下所有设施。"""
        facilities = data_loader.get_facilities_for_destination(destination_id)
        out = []
        for f in facilities:
            out.append({
                "id": f["id"],
                "name": f["name"],
                "category": f["category"],
                "linked_node_id": f.get("linked_node_id"),
                "latitude": f.get("latitude"),
                "longitude": f.get("longitude"),
                "description": f.get("description"),
            })
        dest = data_loader.get_destination_by_id(destination_id)
        return {
            "destination_id": destination_id,
            "internal_map_id": dest["internal_map_id"],
            "count": len(out),
            "facilities": out,
        }
