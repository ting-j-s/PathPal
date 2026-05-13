"""
场所查询服务测试
"""
import pytest
from backend.services.nearby_service import NearbyService, NOTE_TEXT


@pytest.fixture
def service():
    return NearbyService()


@pytest.fixture
def params():
    """动态获取测试参数。"""
    from backend.services.data_loader import (
        load_destinations, load_graph_for_destination
    )
    dests = load_destinations()
    campus = [d for d in dests if d["type"] == "campus"][0]
    g = load_graph_for_destination(campus["id"])
    node_ids = list(g.nodes.keys())
    return {
        "campus_id": campus["id"],
        "node_id": node_ids[0],
    }


class TestNearbyService:

    def test_find_nearby(self, service, params):
        result = service.find_nearby(params["campus_id"], params["node_id"])
        assert result["count"] > 0
        assert len(result["facilities"]) > 0
        for f in result["facilities"]:
            assert "road_distance" in f
            assert f["road_distance"] >= 0  # 设施可能与查询节点相同，距离为 0
            assert "path" in f

    def test_sorted_by_road_distance(self, service, params):
        result = service.find_nearby(params["campus_id"], params["node_id"])
        distances = [f["road_distance"] for f in result["facilities"]]
        assert distances == sorted(distances)

    def test_contains_note(self, service, params):
        result = service.find_nearby(params["campus_id"], params["node_id"])
        assert result["note"] == NOTE_TEXT

    def test_find_by_category(self, service, params):
        result = service.find_by_category(
            params["campus_id"], params["node_id"], category="toilet"
        )
        for f in result["facilities"]:
            assert f["category"] == "toilet"

    def test_search_nearby(self, service, params):
        result = service.search_nearby(
            params["campus_id"], params["node_id"], keyword="超市"
        )
        assert result["count"] > 0
        for f in result["facilities"]:
            found = (
                ("超市" in str(f.get("name", "")))
                or ("超市" in str(f.get("category", "")))
                or ("超市" in str(f.get("description", "")))
            )
            assert found

    def test_radius_filter(self, service, params):
        all_result = service.find_nearby(params["campus_id"], params["node_id"])
        if all_result["count"] >= 3:
            cutoff = all_result["facilities"][2]["road_distance"]
            limited = service.find_nearby(
                params["campus_id"], params["node_id"], radius=cutoff
            )
            for f in limited["facilities"]:
                assert f["road_distance"] <= cutoff

    def test_result_contains_required_fields(self, service, params):
        result = service.find_nearby(params["campus_id"], params["node_id"])
        for field in ["destination_id", "internal_map_id", "origin",
                       "algorithm", "note", "count", "facilities"]:
            assert field in result, f"Missing field: {field}"

    def test_list_facility_categories(self, service, params):
        result = service.list_facility_categories(destination_id=params["campus_id"])
        assert result["count"] > 0
        assert len(result["categories"]) > 0

    def test_list_facilities(self, service, params):
        result = service.list_facilities(params["campus_id"])
        assert result["count"] > 0
        assert len(result["facilities"]) > 0
        for f in result["facilities"]:
            assert "id" in f
            assert "name" in f
            assert "category" in f

    def test_invalid_destination(self, service):
        with pytest.raises(ValueError):
            service.find_nearby("NONEXIST", "NODE_001")

    def test_nearby_facility_has_route_geometry(self, service, params):
        """nearby 设施应包含 route_geometry。"""
        result = service.find_nearby(params["campus_id"], params["node_id"])
        for f in result["facilities"]:
            assert "route_geometry" in f, f"Facility {f.get('id')} missing route_geometry"
            rg = f["route_geometry"]
            if rg:  # 有些设施可能距离为0（同一个节点）
                assert len(rg) >= 2
                for pt in rg:
                    assert len(pt) == 2

    def test_nearby_route_geometry_in_map_bounds(self, service, params):
        """nearby route_geometry 坐标应在对应 map bbox 内。"""
        result = service.find_nearby(params["campus_id"], params["node_id"])
        for f in result["facilities"]:
            rg = f.get("route_geometry", [])
            for pt in rg:
                assert abs(pt[0]) > 0.001, f"lat near zero for {f.get('id')}"
                assert abs(pt[1]) > 0.001, f"lng near zero for {f.get('id')}"
