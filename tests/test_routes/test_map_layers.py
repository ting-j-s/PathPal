"""
地图图层 API 路由测试
"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestMapLayers:

    def test_map_layers_dest_001_returns_full_data(self, client):
        """DEST_001 (BUPT) map-layers 返回完整图层数据，edges 包含 geometry。"""
        resp = client.get("/api/destinations/DEST_001/map-layers")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["destination_id"] == "DEST_001"
        assert data["map_id"] == "MAP_BUPT_REAL"
        assert len(data["nodes"]) >= 20
        assert len(data["edges"]) >= 60
        assert len(data["facilities"]) >= 15
        im = data["internal_map"]
        assert im["is_real_map"] is True
        assert im["show_tile"] is True
        # 验证 edges 有 geometry
        edges_with_geom = [e for e in data["edges"] if e.get("geometry") and len(e["geometry"]) >= 2]
        assert len(edges_with_geom) >= 60

    def test_map_layers_dest_032_returns_full_data(self, client):
        """DEST_032 (天坛) map-layers 返回完整图层数据，edges 包含 geometry。"""
        resp = client.get("/api/destinations/DEST_032/map-layers")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["destination_id"] == "DEST_032"
        assert data["map_id"] == "MAP_SCENIC_REAL"
        assert len(data["nodes"]) >= 20
        assert len(data["edges"]) >= 60
        assert len(data["facilities"]) >= 15
        im = data["internal_map"]
        assert im["is_real_map"] is True
        assert im["show_tile"] is True
        edges_with_geom = [e for e in data["edges"] if e.get("geometry") and len(e["geometry"]) >= 2]
        assert len(edges_with_geom) >= 60

    def test_map_layers_abstract_template(self, client):
        """共享景区模板目的地 (DEST_033 颐和园→MAP_SCENIC_OSM) map-layers 返回 show_tile=false。"""
        resp = client.get("/api/destinations/DEST_033/map-layers")
        assert resp.status_code == 200
        data = resp.get_json()
        im = data["internal_map"]
        assert im["is_real_map"] is False
        assert im["show_tile"] is False
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0

    def test_map_layers_campus_osm_template(self, client):
        """学校OSM模板目的地 (DEST_002 清华大学→MAP_CAMPUS_OSM) map-layers 返回 show_tile=true（白名单覆盖）。"""
        resp = client.get("/api/destinations/DEST_002/map-layers")
        assert resp.status_code == 200
        data = resp.get_json()
        im = data["internal_map"]
        assert im["is_real_map"] is True
        assert im["show_tile"] is True
        assert len(data["nodes"]) >= 20
        assert len(data["edges"]) >= 60

    def test_map_layers_bupt_nodes_in_bounds(self, client):
        """MAP_BUPT_REAL 节点坐标应在北邮范围内。"""
        resp = client.get("/api/destinations/DEST_001/map-layers")
        data = resp.get_json()
        for n in data["nodes"]:
            lat = n.get("latitude", 0)
            lng = n.get("longitude", 0)
            assert 39.949 <= lat <= 39.973, f"{n['id']}: lat {lat} out of BUPT range"
            assert 116.343 <= lng <= 116.370, f"{n['id']}: lng {lng} out of BUPT range"

    def test_map_layers_scenic_nodes_in_bounds(self, client):
        """MAP_SCENIC_REAL 节点坐标应在天坛范围内。"""
        resp = client.get("/api/destinations/DEST_032/map-layers")
        data = resp.get_json()
        for n in data["nodes"]:
            lat = n.get("latitude", 0)
            lng = n.get("longitude", 0)
            assert 39.859 <= lat <= 39.908, f"{n['id']}: lat {lat} out of SCENIC range"
            assert 116.379 <= lng <= 116.439, f"{n['id']}: lng {lng} out of SCENIC range"

    def test_map_layers_edge_nodes_exist(self, client):
        """map-layers 中所有边的 from/to 节点都应存在。"""
        resp = client.get("/api/destinations/DEST_001/map-layers")
        data = resp.get_json()
        node_ids = {n["id"] for n in data["nodes"]}
        for e in data["edges"]:
            assert e["from"] in node_ids, f"Edge {e['id']}: from {e['from']} not in nodes"
            assert e["to"] in node_ids, f"Edge {e['id']}: to {e['to']} not in nodes"

    def test_map_layers_facility_linked_nodes_exist(self, client):
        """map-layers 中所有设施的 linked_node_id 都应存在。"""
        resp = client.get("/api/destinations/DEST_001/map-layers")
        data = resp.get_json()
        node_ids = {n["id"] for n in data["nodes"]}
        for f in data["facilities"]:
            assert f["linked_node_id"] in node_ids, \
                f"Facility {f['id']}: linked_node_id {f['linked_node_id']} not in nodes"

    def test_map_layers_not_found(self, client):
        """不存在的 destination 返回错误。"""
        resp = client.get("/api/destinations/NONEXISTENT/map-layers")
        assert resp.status_code in (400, 404)

    def test_map_layers_has_facility_coords(self, client):
        """map-layers 中设施应有有效坐标。"""
        resp = client.get("/api/destinations/DEST_001/map-layers")
        data = resp.get_json()
        for f in data["facilities"]:
            assert abs(f.get("latitude", 0)) > 0.001 or abs(f.get("longitude", 0)) > 0.001, \
                f"Facility {f['id']}: at (0,0)"
