"""
室内导航服务测试
"""
import pytest
from backend.services.indoor_service import IndoorService


class TestIndoorService:

    @pytest.fixture
    def service(self):
        return IndoorService()

    # ================================================================
    # list_buildings
    # ================================================================

    def test_list_buildings_returns_at_least_two(self, service):
        result = service.list_buildings()
        assert result["count"] >= 2

    def test_list_buildings_has_campus_building(self, service):
        result = service.list_buildings()
        types = {b["building_type"] for b in result["buildings"]}
        assert "campus_building" in types

    def test_list_buildings_has_scenic_exhibition(self, service):
        result = service.list_buildings()
        types = {b["building_type"] for b in result["buildings"]}
        assert "scenic_exhibition" in types

    def test_list_buildings_has_required_fields(self, service):
        result = service.list_buildings()
        for b in result["buildings"]:
            assert "building_id" in b
            assert "building_name" in b
            assert "building_type" in b
            assert "floors" in b
            assert b["node_count"] > 0
            assert b["edge_count"] > 0

    # ================================================================
    # get_building
    # ================================================================

    def test_get_building_returns_full_data(self, service):
        bld = service.get_building("BUILDING_BUPT_TEACHING")
        assert bld["building_id"] == "BUILDING_BUPT_TEACHING"
        assert bld["building_name"] == "北邮教学楼"
        assert bld["building_type"] == "campus_building"
        assert len(bld["floors"]) == 4
        assert len(bld["nodes"]) >= 35
        assert len(bld["edges"]) >= 45

    def test_get_building_scenic(self, service):
        bld = service.get_building("BUILDING_TIANTAN_EXHIBITION")
        assert bld["building_type"] == "scenic_exhibition"
        assert len(bld["floors"]) == 3
        assert len(bld["nodes"]) >= 25
        assert len(bld["edges"]) >= 30

    def test_get_nonexistent_building_raises(self, service):
        with pytest.raises(ValueError):
            service.get_building("NONEXISTENT")

    # ================================================================
    # list_nodes
    # ================================================================

    def test_list_nodes_all(self, service):
        result = service.list_nodes("BUILDING_BUPT_TEACHING")
        assert result["count"] >= 35

    def test_list_nodes_by_floor(self, service):
        result = service.list_nodes("BUILDING_BUPT_TEACHING", floor=1)
        assert result["count"] >= 8
        for n in result["nodes"]:
            assert n["floor"] == 1

    def test_list_nodes_nonexistent_building(self, service):
        with pytest.raises(ValueError):
            service.list_nodes("NONEXISTENT")

    # ================================================================
    # list_floors
    # ================================================================

    def test_list_floors(self, service):
        result = service.list_floors("BUILDING_BUPT_TEACHING")
        assert result["building_id"] == "BUILDING_BUPT_TEACHING"
        assert len(result["floors"]) == 4

    # ================================================================
    # plan_indoor_route
    # ================================================================

    def test_route_gate_to_room_301(self, service):
        """大门到三楼教室301可到达。"""
        result = service.plan_indoor_route(
            "BUILDING_BUPT_TEACHING", "BUPT_T_GATE", "BUPT_T_ROOM_301"
        )
        assert result["reachable"] is True
        assert result["distance"] > 0
        assert len(result["path"]) > 0

    def test_route_has_elevator_or_stairs(self, service):
        """前往高楼层的路径中包含电梯或楼梯。"""
        result = service.plan_indoor_route(
            "BUILDING_BUPT_TEACHING", "BUPT_T_GATE", "BUPT_T_MEET_401"
        )
        assert result["reachable"] is True
        path_types = set()
        for e in result.get("edges", []):
            path_types.add(e.get("type"))
        assert "elevator" in path_types or "stairs" in path_types

    def test_route_returns_steps(self, service):
        """返回步骤列表。"""
        result = service.plan_indoor_route(
            "BUILDING_BUPT_TEACHING", "BUPT_T_GATE", "BUPT_T_ROOM_301"
        )
        assert len(result["steps"]) >= 2
        step_desc = result["steps"][0]["description"]
        assert "出发" in step_desc or "大门" in step_desc

    def test_route_returns_floor_paths(self, service):
        """返回按楼层分组的路径。"""
        result = service.plan_indoor_route(
            "BUILDING_BUPT_TEACHING", "BUPT_T_GATE", "BUPT_T_ROOM_301"
        )
        assert "floor_paths" in result
        assert len(result["floor_paths"]) >= 1

    def test_route_room101_to_office301(self, service):
        """教室101到办公室301可到达。"""
        result = service.plan_indoor_route(
            "BUILDING_BUPT_TEACHING", "BUPT_T_ROOM_101", "BUPT_T_OFF_301"
        )
        assert result["reachable"] is True
        assert result["distance"] > 0

    def test_route_toilet1f_to_office4f(self, service):
        """一层卫生间到四层办公室可到达。"""
        result = service.plan_indoor_route(
            "BUILDING_BUPT_TEACHING", "BUPT_T_TOILET_1F", "BUPT_T_OFF_401"
        )
        assert result["reachable"] is True
        assert result["distance"] > 0

    # --- 景区展馆测试 ---

    def test_route_scenic_gate_to_exhibit5(self, service):
        """展馆入口到展厅5可到达。"""
        result = service.plan_indoor_route(
            "BUILDING_TIANTAN_EXHIBITION", "TTE_GATE", "TTE_EXHIBIT_5"
        )
        assert result["reachable"] is True
        assert result["distance"] > 0

    def test_route_scenic_service_to_viewpoint(self, service):
        """服务台到观景点可到达。"""
        result = service.plan_indoor_route(
            "BUILDING_TIANTAN_EXHIBITION", "TTE_SERVICE", "TTE_VIEW_2F"
        )
        assert result["reachable"] is True
        assert result["distance"] > 0

    def test_route_scenic_shop_to_office(self, service):
        """文创商店到管理办公室可到达。"""
        result = service.plan_indoor_route(
            "BUILDING_TIANTAN_EXHIBITION", "TTE_SHOP", "TTE_OFFICE_M"
        )
        assert result["reachable"] is True
        assert result["distance"] > 0

    # --- 错误处理 ---

    def test_route_nonexistent_building(self, service):
        with pytest.raises(ValueError):
            service.plan_indoor_route("NONEXISTENT", "A", "B")

    def test_route_nonexistent_start(self, service):
        with pytest.raises(ValueError):
            service.plan_indoor_route(
                "BUILDING_BUPT_TEACHING", "NONEXISTENT", "BUPT_T_GATE"
            )

    def test_route_nonexistent_end(self, service):
        with pytest.raises(ValueError):
            service.plan_indoor_route(
                "BUILDING_BUPT_TEACHING", "BUPT_T_GATE", "NONEXISTENT"
            )

    # --- 结果字段完整性 ---

    def test_route_result_has_required_fields(self, service):
        result = service.plan_indoor_route(
            "BUILDING_BUPT_TEACHING", "BUPT_T_GATE", "BUPT_T_ROOM_201"
        )
        for field in ["building_id", "building_name", "building_type",
                       "strategy", "algorithm", "reachable", "path",
                       "distance", "nodes", "edges", "steps", "floor_paths"]:
            assert field in result, f"Missing field: {field}"

    def test_route_nodes_have_coordinates(self, service):
        """路径上的节点都有 x, y 坐标。"""
        result = service.plan_indoor_route(
            "BUILDING_BUPT_TEACHING", "BUPT_T_GATE", "BUPT_T_ROOM_201"
        )
        for n in result["nodes"]:
            assert "x" in n
            assert "y" in n
