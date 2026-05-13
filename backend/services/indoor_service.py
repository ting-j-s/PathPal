"""
PathPal 室内导航服务（简单 Demo）
基于 indoor_graphs.json 提供最小室内导航功能。
"""
from backend.services import data_loader
from backend.algorithms.graph import Graph
from backend.algorithms.dijkstra import dijkstra_shortest_distance


class IndoorService:

    def list_buildings(self):
        """列出所有室内建筑。"""
        indoor_data = data_loader.load_indoor_graphs()
        indoor_maps = indoor_data.get("indoor_maps", [])
        buildings = []
        for m in indoor_maps:
            buildings.append({
                "building_id": m.get("building_id"),
                "name": m.get("name"),
                "floors": m.get("floors"),
                "node_count": len(m.get("nodes", [])),
                "edge_count": len(m.get("edges", [])),
            })
        return {
            "count": len(buildings),
            "buildings": buildings,
            "note": "室内导航为简单 Demo 功能",
        }

    def get_building(self, building_id):
        """获取单个建筑详情。"""
        indoor_data = data_loader.load_indoor_graphs()
        for m in indoor_data.get("indoor_maps", []):
            if m.get("building_id") == building_id:
                return {
                    "building_id": m["building_id"],
                    "name": m["name"],
                    "floors": m.get("floors"),
                    "node_count": len(m.get("nodes", [])),
                    "edge_count": len(m.get("edges", [])),
                    "nodes": [
                        {"id": n["id"], "name": n.get("name"), "floor": n.get("floor")}
                        for n in m.get("nodes", [])
                    ],
                }
        raise ValueError(f"Building not found: {building_id}")

    def plan_indoor_route(self, building_id, start, end):
        """室内最短路径规划。"""
        indoor_data = data_loader.load_indoor_graphs()
        building = None
        for m in indoor_data.get("indoor_maps", []):
            if m.get("building_id") == building_id:
                building = m
                break

        if building is None:
            raise ValueError(f"Building not found: {building_id}")

        # 构建临时图
        g = Graph(map_id=building_id)
        for node in building.get("nodes", []):
            g.add_node(node["id"], node)
        for edge in building.get("edges", []):
            if g.has_node(edge.get("from")) and g.has_node(edge.get("to")):
                g.add_edge(edge)

        result = dijkstra_shortest_distance(g, start, end)

        steps = []
        for seg in result.get("segments", []):
            steps.append({
                "from": seg["from"],
                "to": seg["to"],
                "from_name": seg["from_name"],
                "to_name": seg["to_name"],
                "distance": seg["distance"],
            })

        return {
            "building_id": building_id,
            "building_name": building.get("name"),
            "algorithm": "Dijkstra (Indoor Graph)",
            "reachable": result["reachable"],
            "path": result.get("path", []),
            "total_distance": result.get("total_distance"),
            "steps": steps,
        }
