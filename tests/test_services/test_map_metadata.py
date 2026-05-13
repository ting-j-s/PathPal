"""
地图元数据服务测试
"""
import pytest
from backend.services.data_loader import (
    load_internal_maps,
    load_internal_nodes,
    load_facilities,
    get_internal_map_by_id,
    get_internal_map_for_destination,
    get_destination_by_id,
    get_map_id_by_destination_id,
)


class TestMapMetadata:

    def test_maps_have_new_fields(self):
        maps = load_internal_maps()
        for m in maps:
            mid = m.get("map_id") or m.get("id")
            assert "source" in m, f"{mid}: missing source"
            assert "is_real_map" in m, f"{mid}: missing is_real_map"
            assert "show_tile" in m, f"{mid}: missing show_tile"
            assert "center" in m, f"{mid}: missing center"
            assert "tile_note" in m, f"{mid}: missing tile_note"

    def test_map_bupt_real_exists(self):
        m = get_internal_map_by_id("MAP_BUPT_REAL")
        assert m["type"] == "campus"
        assert m["is_real_map"] is True
        assert m["show_tile"] is True
        assert m["source"] in ("openstreetmap_vector", "openstreetmap")
        assert "sightseeing_car" not in m["supported_transports"]

    def test_map_scenic_real_exists(self):
        m = get_internal_map_by_id("MAP_SCENIC_REAL")
        assert m["type"] == "attraction"
        assert m["is_real_map"] is True
        assert m["show_tile"] is True
        assert m["source"] in ("openstreetmap_vector", "openstreetmap")
        assert "bike" not in m["supported_transports"]

    def test_simulated_maps_no_tile(self):
        maps = load_internal_maps()
        simulated = [m for m in maps if not m.get("is_real_map")]
        assert len(simulated) >= 3
        for m in simulated:
            assert m["show_tile"] is False, f"{m.get('map_id')}: simulated map should have show_tile=false"
            assert m["is_real_map"] is False

    def test_real_maps_show_tile(self):
        maps = load_internal_maps()
        real = [m for m in maps if m.get("is_real_map")]
        assert len(real) == 2
        for m in real:
            assert m["show_tile"] is True, f"{m.get('map_id')}: real map should have show_tile=true"

    def test_get_map_for_bupt_destination(self):
        m = get_internal_map_for_destination("DEST_001")
        assert m.get("map_id") == "MAP_BUPT_REAL"

    def test_get_map_for_temple_of_heaven(self):
        m = get_internal_map_for_destination("DEST_032")
        assert m.get("map_id") == "MAP_SCENIC_REAL"

    def test_nonexistent_map_raises(self):
        with pytest.raises(ValueError):
            get_internal_map_by_id("NONEXISTENT_MAP")

    def test_bupt_coordinate_bounds(self):
        """MAP_BUPT_REAL 所有节点坐标应在北邮范围内。"""
        nodes = [n for n in load_internal_nodes() if n.get("map_id") == "MAP_BUPT_REAL"]
        assert len(nodes) >= 20
        for n in nodes:
            lat = n.get("latitude", 0)
            lng = n.get("longitude", 0)
            assert 39.952 <= lat <= 39.970, f"{n['id']}: lat {lat} outside BUPT range"
            assert 116.347 <= lng <= 116.366, f"{n['id']}: lng {lng} outside BUPT range"

    def test_scenic_coordinate_bounds(self):
        """MAP_SCENIC_REAL 所有节点坐标应在天坛范围内。"""
        nodes = [n for n in load_internal_nodes() if n.get("map_id") == "MAP_SCENIC_REAL"]
        assert len(nodes) >= 20
        for n in nodes:
            lat = n.get("latitude", 0)
            lng = n.get("longitude", 0)
            assert 39.864 <= lat <= 39.903, f"{n['id']}: lat {lat} outside SCENIC range"
            assert 116.385 <= lng <= 116.433, f"{n['id']}: lng {lng} outside SCENIC range"

    def test_no_facilities_at_zero_zero(self):
        """任何设施不应有 (0,0) 坐标。"""
        for f in load_facilities():
            lat = f.get("latitude", 0)
            lng = f.get("longitude", 0)
            assert abs(lat) > 0.001 or abs(lng) > 0.001, \
                f"{f['id']}: facility at (0,0)"

    def test_map_layers_dest_001(self):
        """DEST_001 → MAP_BUPT_REAL -> 应有节点、边、设施。"""
        dest = get_destination_by_id("DEST_001")
        map_id = dest["internal_map_id"]
        assert map_id == "MAP_BUPT_REAL"
        nodes = [n for n in load_internal_nodes() if n.get("map_id") == map_id]
        edges = __import__("json").load(open(__import__("pathlib").Path(__file__).parent.parent.parent / "data" / "internal_edges.json"))
        edges = [e for e in edges if e.get("map_id") == map_id]
        facs = [f for f in load_facilities() if f.get("map_id") == map_id]
        assert len(nodes) >= 20
        assert len(edges) >= 60
        assert len(facs) >= 15

    def test_map_layers_dest_032(self):
        """DEST_032 → MAP_SCENIC_REAL -> 应有节点、边、设施。"""
        dest = get_destination_by_id("DEST_032")
        map_id = dest["internal_map_id"]
        assert map_id == "MAP_SCENIC_REAL"
        nodes = [n for n in load_internal_nodes() if n.get("map_id") == map_id]
        edges = __import__("json").load(open(__import__("pathlib").Path(__file__).parent.parent.parent / "data" / "internal_edges.json"))
        edges = [e for e in edges if e.get("map_id") == map_id]
        facs = [f for f in load_facilities() if f.get("map_id") == map_id]
        assert len(nodes) >= 20
        assert len(edges) >= 60
        assert len(facs) >= 15
