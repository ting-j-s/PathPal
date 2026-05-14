"""
PathPal 室内导航服务
基于 indoor_graphs.json 提供室内导航功能。
支持多建筑、跨楼层路径规划（电梯/楼梯）、楼层拓扑查询。
"""
from backend.services import data_loader
from backend.algorithms.indoor_dijkstra import indoor_dijkstra


class IndoorService:

    # ================================================================
    # 建筑列表与查询
    # ================================================================

    def list_buildings(self):
        """列出所有室内建筑的基本信息。"""
        indoor_data = data_loader.load_indoor_graphs()
        indoor_maps = indoor_data.get("indoor_maps", [])
        buildings = []
        for m in indoor_maps:
            nodes = m.get("nodes", [])
            edges = m.get("edges", [])
            buildings.append({
                "building_id": m.get("building_id"),
                "building_name": m.get("building_name"),
                "building_type": m.get("building_type"),
                "destination_id": m.get("destination_id"),
                "description": m.get("description"),
                "floors": m.get("floors", []),
                "node_count": len(nodes),
                "edge_count": len(edges),
            })
        return {
            "count": len(buildings),
            "buildings": buildings,
        }

    def get_building(self, building_id):
        """获取单个建筑的完整数据（含节点和边）。"""
        building = self._find_building(building_id)
        return dict(building)

    def _find_building(self, building_id):
        indoor_data = data_loader.load_indoor_graphs()
        for m in indoor_data.get("indoor_maps", []):
            if m.get("building_id") == building_id:
                return m
        raise ValueError(f"Building not found: {building_id}")

    # ================================================================
    # 节点查询
    # ================================================================

    def list_nodes(self, building_id, floor=None):
        """返回建筑内节点，可按楼层过滤。"""
        building = self._find_building(building_id)
        nodes = building.get("nodes", [])
        if floor is not None:
            floor = int(floor)
            nodes = [n for n in nodes if n.get("floor") == floor]
        return {
            "building_id": building_id,
            "floor": floor,
            "count": len(nodes),
            "nodes": nodes,
        }

    def list_floors(self, building_id):
        """返回建筑的所有楼层和每层节点数。"""
        building = self._find_building(building_id)
        nodes = building.get("nodes", [])
        floor_counts = {}
        for n in nodes:
            f = str(n.get("floor", 1))
            floor_counts[f] = floor_counts.get(f, 0) + 1
        return {
            "building_id": building_id,
            "floors": building.get("floors", []),
            "floor_node_counts": floor_counts,
        }

    # ================================================================
    # 路径规划
    # ================================================================

    def plan_indoor_route(self, building_id, start, end, strategy="shortest_distance"):
        """室内路径规划。"""
        building = self._find_building(building_id)

        node_ids = {n["id"] for n in building.get("nodes", [])}
        if start not in node_ids:
            raise ValueError(f"Start node not found in building: {start}")
        if end not in node_ids:
            raise ValueError(f"End node not found in building: {end}")

        result = indoor_dijkstra(building, start, end)

        return {
            "building_id": building_id,
            "building_name": building.get("building_name"),
            "building_type": building.get("building_type"),
            "strategy": strategy,
            "algorithm": "Indoor Dijkstra",
            "reachable": result["reachable"],
            "path": result["path"],
            "distance": result["distance"],
            "nodes": result["nodes"],
            "edges": result["edges"],
            "steps": result["steps"],
            "floor_paths": result["floor_paths"],
        }
