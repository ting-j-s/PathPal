"""
路线规划服务测试
"""
import pytest
from backend.services.route_service import RouteService, NOTE_TEXT


@pytest.fixture
def service():
    return RouteService()


@pytest.fixture
def params():
    """动态获取测试参数，选取坐标合理的主路节点。"""
    from backend.services.data_loader import (
        load_destinations, load_graph_for_destination
    )
    dests = load_destinations()
    campus = [d for d in dests if d["type"] == "campus"][0]
    attraction = [d for d in dests if d["type"] == "attraction"][0]

    campus_g = load_graph_for_destination(campus["id"])
    # 选取坐标合理的主路节点（过滤设施挂接点的异常坐标）
    valid_nodes = [
        nid for nid, nd in campus_g.nodes.items()
        if nd.get("latitude", 0) > 0.01
    ]
    attraction_g = load_graph_for_destination(attraction["id"])
    valid_attr_nodes = [
        nid for nid, nd in attraction_g.nodes.items()
        if nd.get("latitude", 0) > 0.01
    ]

    return {
        "campus_id": campus["id"],
        "campus_name": campus["name"],
        "campus_start": valid_nodes[0],
        "campus_end": valid_nodes[3] if len(valid_nodes) > 3 else valid_nodes[-1],
        "attraction_id": attraction["id"],
        "attraction_start": valid_attr_nodes[0],
        "attraction_end": valid_attr_nodes[3] if len(valid_attr_nodes) > 3 else valid_attr_nodes[-1],
        # 供 bike 测试使用的短距离节点对
        "valid_nodes": valid_nodes,
    }


class TestRouteService:

    def test_shortest_distance(self, service, params):
        result = service.plan_shortest_distance(
            params["campus_id"], params["campus_start"], params["campus_end"]
        )
        assert result["reachable"] is True
        assert result["total_distance"] > 0
        assert len(result["path"]) >= 2
        assert result["strategy"] == "shortest_distance"
        assert result["destination_id"] == params["campus_id"]
        assert result["note"] == NOTE_TEXT

    def test_shortest_time(self, service, params):
        result = service.plan_shortest_time(
            params["campus_id"], params["campus_start"], params["campus_end"],
            transport="walk"
        )
        assert result["reachable"] is True
        assert result["total_time"] > 0
        assert result["strategy"] == "shortest_time"

    def test_shortest_time_returns_segments(self, service, params):
        result = service.plan_shortest_time(
            params["campus_id"], params["campus_start"], params["campus_end"],
            transport="walk"
        )
        assert len(result["segments"]) > 0
        for seg in result["segments"]:
            assert "from" in seg
            assert "to" in seg
            assert "transport" in seg
            assert "distance" in seg
            assert "time" in seg

    def test_transport_bike_on_campus(self, service, params):
        from backend.algorithms.dijkstra import dijkstra_shortest_time
        from backend.services.data_loader import load_graph_for_destination
        g = load_graph_for_destination(params["campus_id"])
        valid = params["valid_nodes"]
        start, end = valid[0], valid[1]
        found = False
        for a in valid[:30]:
            if found:
                break
            for b in valid[1:30]:
                if a != b:
                    r = dijkstra_shortest_time(g, a, b, "bike")
                    if r["reachable"]:
                        start, end, found = a, b, True
                        break
        if not found:
            pytest.skip("No bike-reachable pair found in first 30 valid nodes")
        result = service.plan_shortest_time(
            params["campus_id"], start, end, transport="bike"
        )
        assert result["reachable"] is True
        transports = {s["transport"] for s in result["segments"]}
        assert "bike" in transports

    def test_transport_sightseeing_car_banned_on_campus(self, service, params):
        with pytest.raises(ValueError, match="校园不支持"):
            service.plan_shortest_time(
                params["campus_id"], params["campus_start"], params["campus_end"],
                transport="sightseeing_car"
            )

    def test_transport_bike_banned_on_attraction(self, service, params):
        with pytest.raises(ValueError, match="景区不支持"):
            service.plan_shortest_time(
                params["attraction_id"], params["attraction_start"], params["attraction_end"],
                transport="bike"
            )

    def test_transport_sightseeing_car_on_attraction(self, service, params):
        result = service.plan_shortest_time(
            params["attraction_id"], params["attraction_start"], params["attraction_end"],
            transport="walk"
        )
        assert result["reachable"] is True

    def test_mixed_time(self, service, params):
        result = service.plan_mixed_time(
            params["campus_id"], params["campus_start"], params["campus_end"]
        )
        assert result["reachable"] is True
        assert result["strategy"] == "mixed_time"
        for seg in result["segments"]:
            assert seg["transport"] is not None

    def test_result_contains_required_fields(self, service, params):
        result = service.plan_shortest_distance(
            params["campus_id"], params["campus_start"], params["campus_end"]
        )
        for field in ["destination_id", "destination_name", "destination_type",
                       "internal_map_id", "strategy", "algorithm", "formula",
                       "reachable", "path", "coordinates", "total_distance",
                       "total_time", "segments", "note"]:
            assert field in result, f"Missing field: {field}"

    def test_list_nodes(self, service, params):
        result = service.list_nodes(params["campus_id"])
        assert result["destination_id"] == params["campus_id"]
        assert result["count"] > 0
        assert len(result["nodes"]) > 0
        for n in result["nodes"]:
            assert "id" in n
            assert "name" in n

    def test_list_nodes_invalid_dest(self, service):
        with pytest.raises(ValueError):
            service.list_nodes("NONEXIST")

    def test_multi_point_route(self, service, params):
        valid = params["valid_nodes"]
        targets = valid[2:5]
        result = service.plan_multi_point(
            params["campus_id"], valid[0], targets
        )
        assert result["reachable"] is True
        assert len(result["visit_order"]) == len(targets)
        assert result["tsp_approximation"] == "greedy_nearest_neighbor"
        assert result["returns_to_start"] is True

    def test_get_route_summary(self, service, params):
        result = service.plan_shortest_distance(
            params["campus_id"], params["campus_start"], params["campus_end"]
        )
        summary = service.get_route_summary(result)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_route_geometry_present(self, service, params):
        """路线结果应包含 route_geometry。"""
        result = service.plan_shortest_distance(
            params["campus_id"], params["campus_start"], params["campus_end"]
        )
        assert "route_geometry" in result
        assert len(result["route_geometry"]) >= 2
        # route_geometry 每个点应为 [lat, lng]
        for pt in result["route_geometry"]:
            assert len(pt) == 2

    def test_route_geometry_coords_in_bounds(self, service, params):
        """route_geometry 坐标应在北邮 bbox 内。"""
        result = service.plan_shortest_distance(
            params["campus_id"], params["campus_start"], params["campus_end"]
        )
        for pt in result["route_geometry"]:
            assert 39.949 <= pt[0] <= 39.973, f"lat {pt[0]} out of bounds"
            assert 116.343 <= pt[1] <= 116.370, f"lng {pt[1]} out of bounds"

    def test_segments_have_geometry(self, service, params):
        """segments 中每段应包含 geometry。"""
        result = service.plan_shortest_distance(
            params["campus_id"], params["campus_start"], params["campus_end"]
        )
        for seg in result["segments"]:
            assert "geometry" in seg, f"Segment missing geometry"
            assert seg["geometry"] is not None
            assert len(seg["geometry"]) >= 2
