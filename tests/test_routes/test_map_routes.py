"""
内部地图 API 路由测试
"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestMapRoutes:

    def test_list_internal_maps(self, client):
        resp = client.get("/api/internal-maps")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 5
        assert len(data["maps"]) == 5
        for m in data["maps"]:
            assert "map_id" in m
            assert "is_real_map" in m
            assert "show_tile" in m
            assert "center" in m

    def test_get_map_by_id_bupt(self, client):
        resp = client.get("/api/internal-maps/MAP_BUPT_REAL")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["map_id"] == "MAP_BUPT_REAL"
        assert data["is_real_map"] is True
        assert data["show_tile"] is True

    def test_get_map_by_id_scenic(self, client):
        resp = client.get("/api/internal-maps/MAP_SCENIC_REAL")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["map_id"] == "MAP_SCENIC_REAL"
        assert data["is_real_map"] is True
        assert data["show_tile"] is True

    def test_get_map_by_id_not_found(self, client):
        resp = client.get("/api/internal-maps/NONEXISTENT")
        assert resp.status_code == 404

    def test_route_nodes_includes_map_meta(self, client):
        resp = client.get("/api/route/nodes?destination_id=DEST_001")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "internal_map" in data
        assert data["internal_map"]["is_real_map"] is True
        assert data["internal_map"]["show_tile"] is True

    def test_nearby_includes_map_meta(self, client):
        # Get a valid node for DEST_001 (BUPT) first
        resp = client.get("/api/route/nodes?destination_id=DEST_001")
        nodes = resp.get_json()["nodes"]
        valid = [n for n in nodes if n.get("latitude", 0) > 0.01]
        node_id = valid[0]["id"]
        resp2 = client.get(f"/api/nearby?destination_id=DEST_001&node_id={node_id}")
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert "internal_map" in data2
        assert data2["internal_map"]["is_real_map"] is True
