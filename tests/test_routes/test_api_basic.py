"""
API 基本测试（使用 Flask test_client）
"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_ids():
    """动态获取测试用的有效 ID（选取坐标合理的节点）。"""
    from backend.services.data_loader import (
        load_destinations, load_graph_for_destination
    )
    dests = load_destinations()
    campus = [d for d in dests if d["type"] == "campus"][0]

    g = load_graph_for_destination(campus["id"])
    # 过滤坐标异常的设施挂接点
    valid = [
        nid for nid, nd in g.nodes.items()
        if nd.get("latitude", 0) > 0.01
    ]

    return {
        "campus_id": campus["id"],
        "node_a": valid[0],
        "node_b": valid[3] if len(valid) > 3 else valid[-1],
        "valid_nodes": valid,
    }


class TestBasicAPI:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["project"] == "PathPal"

    def test_stats(self, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["destinations"] == 217
        assert data["internal_maps"] == 3
        assert data["internal_edges"] == 284


class TestRecommendationAPI:
    def test_hot_recommendations(self, client):
        resp = client.get("/api/recommendations/hot?k=5")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 5

    def test_rating_recommendations(self, client):
        resp = client.get("/api/recommendations/rating?k=5")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 5

    def test_interest_recommendations(self, client):
        resp = client.get("/api/recommendations/interest?user_id=USER_001&k=5")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user_id"] == "USER_001"
        assert data["count"] == 5

    def test_search_destinations(self, client):
        resp = client.get("/api/destinations/search?keyword=北京")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] > 0

    def test_list_destinations(self, client):
        resp = client.get("/api/destinations")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 217

    def test_get_destination(self, client):
        resp = client.get("/api/destinations/DEST_001")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["result"]["id"] == "DEST_001"

    def test_get_destination_invalid(self, client):
        resp = client.get("/api/destinations/NONEXIST")
        assert resp.status_code == 400

    def test_filter_by_category(self, client):
        resp = client.get("/api/destinations/category?category=park")
        assert resp.status_code == 200

    def test_search_missing_keyword(self, client):
        resp = client.get("/api/destinations/search")
        assert resp.status_code == 400

    def test_interest_missing_user_id(self, client):
        resp = client.get("/api/recommendations/interest")
        assert resp.status_code == 400


class TestRouteAPI:
    def test_list_nodes(self, client, test_ids):
        resp = client.get(f"/api/route/nodes?destination_id={test_ids['campus_id']}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] > 0

    def test_shortest_distance(self, client, test_ids):
        url = (f"/api/route/shortest-distance?destination_id={test_ids['campus_id']}"
               f"&start={test_ids['node_a']}&end={test_ids['node_b']}")
        resp = client.get(url)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["reachable"] is True
        assert data["note"]

    def test_mixed_time(self, client, test_ids):
        url = (f"/api/route/mixed-time?destination_id={test_ids['campus_id']}"
               f"&start={test_ids['node_a']}&end={test_ids['node_b']}")
        resp = client.get(url)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["reachable"] is True

    def test_missing_destination_id(self, client):
        resp = client.get("/api/route/nodes")
        assert resp.status_code == 400

    def test_invalid_destination(self, client):
        resp = client.get("/api/route/nodes?destination_id=NONEXIST")
        assert resp.status_code == 400

    def test_multi_point(self, client, test_ids):
        resp = client.post("/api/route/multi-point", json={
            "destination_id": test_ids["campus_id"],
            "start": test_ids["valid_nodes"][0],
            "targets": [test_ids["valid_nodes"][2], test_ids["valid_nodes"][3]],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["reachable"] is True


class TestNearbyAPI:
    def test_nearby(self, client, test_ids):
        resp = client.get(
            f"/api/nearby?destination_id={test_ids['campus_id']}"
            f"&node_id={test_ids['node_a']}"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] > 0
        assert data["note"]

    def test_nearby_categories(self, client, test_ids):
        resp = client.get(f"/api/nearby/categories?destination_id={test_ids['campus_id']}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] > 0

    def test_nearby_facilities(self, client, test_ids):
        resp = client.get(f"/api/nearby/facilities?destination_id={test_ids['campus_id']}")
        assert resp.status_code == 200

    def test_nearby_missing_params(self, client):
        resp = client.get("/api/nearby")
        assert resp.status_code == 400


class TestIndoorAPI:
    def test_buildings(self, client):
        resp = client.get("/api/indoor/buildings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1

    def test_indoor_route(self, client):
        resp = client.get(
            "/api/indoor/route?building_id=BUILDING_BUPT_MAIN"
            "&start=IN_B101&end=IN_B201"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["reachable"] is True
