"""
室内导航 API 路由测试
"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestIndoorRoutes:

    # ================================================================
    # GET /api/indoor/buildings
    # ================================================================

    def test_list_buildings(self, client):
        resp = client.get("/api/indoor/buildings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] >= 2
        for b in data["buildings"]:
            assert "building_id" in b
            assert "building_name" in b
            assert "building_type" in b

    # ================================================================
    # GET /api/indoor/buildings/<building_id>
    # ================================================================

    def test_get_building_campus(self, client):
        resp = client.get("/api/indoor/buildings/BUILDING_BUPT_TEACHING")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["building_name"] == "北邮教学楼"
        assert data["building_type"] == "campus_building"
        assert len(data["nodes"]) >= 35
        assert len(data["edges"]) >= 45

    def test_get_building_scenic(self, client):
        resp = client.get("/api/indoor/buildings/BUILDING_TIANTAN_EXHIBITION")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["building_name"] == "天坛展馆"
        assert data["building_type"] == "scenic_exhibition"

    def test_get_building_not_found(self, client):
        resp = client.get("/api/indoor/buildings/NONEXISTENT")
        assert resp.status_code == 404

    # ================================================================
    # GET /api/indoor/nodes
    # ================================================================

    def test_list_nodes(self, client):
        resp = client.get("/api/indoor/nodes?building_id=BUILDING_BUPT_TEACHING")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] >= 35
        for n in data["nodes"]:
            assert "id" in n
            assert "floor" in n
            assert "type" in n

    def test_list_nodes_by_floor(self, client):
        resp = client.get("/api/indoor/nodes?building_id=BUILDING_BUPT_TEACHING&floor=1")
        assert resp.status_code == 200
        data = resp.get_json()
        for n in data["nodes"]:
            assert n["floor"] == 1

    def test_list_nodes_missing_building_id(self, client):
        resp = client.get("/api/indoor/nodes")
        assert resp.status_code == 400

    def test_list_nodes_not_found(self, client):
        resp = client.get("/api/indoor/nodes?building_id=NONEXISTENT")
        assert resp.status_code == 404

    # ================================================================
    # GET /api/indoor/floors
    # ================================================================

    def test_list_floors(self, client):
        resp = client.get("/api/indoor/floors?building_id=BUILDING_BUPT_TEACHING")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["floors"] == [1, 2, 3, 4]
        assert len(data["floor_node_counts"]) == 4

    # ================================================================
    # GET /api/indoor/route
    # ================================================================

    def test_route_gate_to_room(self, client):
        resp = client.get(
            "/api/indoor/route?building_id=BUILDING_BUPT_TEACHING"
            "&start=BUPT_T_GATE&end=BUPT_T_ROOM_301"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["reachable"] is True
        assert data["distance"] > 0
        assert len(data["path"]) > 0
        assert data["algorithm"] == "Indoor Dijkstra"
        assert data["strategy"] == "shortest_distance"

    def test_route_returns_steps(self, client):
        resp = client.get(
            "/api/indoor/route?building_id=BUILDING_BUPT_TEACHING"
            "&start=BUPT_T_GATE&end=BUPT_T_ROOM_301"
        )
        data = resp.get_json()
        assert len(data["steps"]) >= 1

    def test_route_scenic(self, client):
        resp = client.get(
            "/api/indoor/route?building_id=BUILDING_TIANTAN_EXHIBITION"
            "&start=TTE_GATE&end=TTE_EXHIBIT_5"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["reachable"] is True

    def test_route_missing_params(self, client):
        resp = client.get("/api/indoor/route?building_id=X")
        assert resp.status_code == 400

    def test_route_building_not_found(self, client):
        resp = client.get(
            "/api/indoor/route?building_id=NONEXISTENT"
            "&start=A&end=B"
        )
        assert resp.status_code == 400

    def test_route_nonexistent_node(self, client):
        resp = client.get(
            "/api/indoor/route?building_id=BUILDING_BUPT_TEACHING"
            "&start=NONEXISTENT&end=BUPT_T_GATE"
        )
        assert resp.status_code == 400
