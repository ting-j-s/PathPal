"""
PathPal 路线规划服务
封装景区/校园内部路线规划，所有路线仅在同一 internal_map_id 内进行。
"""
from backend.services import data_loader
from backend.algorithms.dijkstra import (
    dijkstra_shortest_distance,
    dijkstra_shortest_time,
    dijkstra_mixed_time,
    multi_point_route,
    extract_route_geometry,
)
from backend.algorithms.nearby import extract_path_coordinates

NOTE_TEXT = "路线规划仅在景区/校园内部道路图中进行，不是城市级外部导航"


class RouteService:

    def _validate_transport(self, dest_type, transport):
        """校验交通工具是否允许。"""
        if dest_type == "campus":
            if transport == "sightseeing_car":
                raise ValueError("校园不支持观光车（sightseeing_car），请使用 walk 或 bike")
        elif dest_type == "attraction":
            if transport == "bike":
                raise ValueError("景区不支持自行车（bike），请使用 walk 或 sightseeing_car")

    def _make_result(self, dest_id, strategy, formula, route_result):
        """构建统一返回格式。"""
        dest = data_loader.get_destination_by_id(dest_id)
        graph = data_loader.load_graph_for_destination(dest_id)
        segments = route_result.get("segments", [])
        route_geometry = extract_route_geometry(segments)
        return {
            "destination_id": dest_id,
            "destination_name": dest["name"],
            "destination_type": dest["type"],
            "internal_map_id": dest["internal_map_id"],
            "strategy": strategy,
            "algorithm": "Dijkstra",
            "formula": formula,
            "reachable": route_result["reachable"],
            "path": route_result.get("path", []),
            "coordinates": extract_path_coordinates(graph, route_result.get("path", [])),
            "route_geometry": route_geometry,
            "total_distance": route_result.get("total_distance"),
            "total_time": route_result.get("total_time"),
            "segments": segments,
            "note": NOTE_TEXT,
        }

    def plan_shortest_distance(self, destination_id, start, end):
        """最短距离路线。"""
        graph = data_loader.load_graph_for_destination(destination_id)
        result = dijkstra_shortest_distance(graph, start, end)
        return self._make_result(
            destination_id, "shortest_distance",
            "weight = distance",
            result,
        )

    def plan_shortest_time(self, destination_id, start, end, transport="walk"):
        """指定交通工具最短时间。"""
        dest_type = data_loader.get_destination_type(destination_id)
        self._validate_transport(dest_type, transport)
        graph = data_loader.load_graph_for_destination(destination_id)
        result = dijkstra_shortest_time(graph, start, end, transport)
        return self._make_result(
            destination_id, "shortest_time",
            f"time = distance / (congestion × ideal_speed_{transport})",
            result,
        )

    def plan_mixed_time(self, destination_id, start, end):
        """混合交通最短时间。"""
        dest = data_loader.get_destination_by_id(destination_id)
        graph = data_loader.load_graph_for_destination(destination_id)
        result = dijkstra_mixed_time(graph, start, end, dest["type"])
        return self._make_result(
            destination_id, "mixed_time",
            "每边自动选择最快交通工具",
            result,
        )

    def plan_multi_point(self, destination_id, start, targets, strategy="shortest_distance"):
        """多点路线计划（贪心 TSP 近似）。"""
        dest = data_loader.get_destination_by_id(destination_id)
        graph = data_loader.load_graph_for_destination(destination_id)
        result = multi_point_route(graph, start, targets, strategy, dest["type"])

        out = self._make_result(destination_id, strategy, "", result)
        out["tsp_approximation"] = "greedy_nearest_neighbor"
        out["returns_to_start"] = True
        out["visit_order"] = result.get("visit_order", [])
        return out

    def list_nodes(self, destination_id):
        """返回该目的地内部地图所有节点，附带 internal_map 元数据。"""
        dest = data_loader.get_destination_by_id(destination_id)
        internal_map = data_loader.get_internal_map_for_destination(destination_id)
        nodes = data_loader.get_nodes_for_destination(destination_id)
        formatted = []
        for n in nodes:
            formatted.append({
                "id": n["id"],
                "name": n["name"],
                "type": n.get("type"),
                "latitude": n.get("latitude"),
                "longitude": n.get("longitude"),
            })
        return {
            "destination_id": destination_id,
            "destination_name": dest["name"],
            "internal_map_id": dest["internal_map_id"],
            "internal_map": {
                "is_real_map": internal_map.get("is_real_map", False),
                "show_tile": internal_map.get("show_tile", False),
                "center": internal_map.get("center"),
                "tile_note": internal_map.get("tile_note"),
            },
            "count": len(formatted),
            "nodes": formatted,
        }

    def get_route_summary(self, result):
        """生成简短中文路线说明。"""
        if not result.get("reachable"):
            return "无法到达目的地。"
        dist = result.get("total_distance", 0)
        time = result.get("total_time", 0)
        seg_count = len(result.get("segments", []))
        transports = set(s.get("transport") for s in result.get("segments", []) if s.get("transport"))
        transport_str = "、".join(sorted(transports)) if transports else "步行"
        return (
            f"路线规划完成：共 {seg_count} 段，"
            f"总距离约 {dist:.0f} 米，"
            f"预计时间约 {time / 60:.1f} 分钟，"
            f"使用交通工具：{transport_str}"
        )
