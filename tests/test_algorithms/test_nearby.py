"""
附近设施查询测试
"""
import pytest
from backend.algorithms.graph import load_graph_from_data
from backend.algorithms.nearby import (
    calculate_nearby_facilities_by_road_distance,
    validate_facilities_same_map,
    extract_path_coordinates,
)
from backend.algorithms.search import filter_by_map_id


class TestNearbyFacilities:
    @pytest.fixture(autouse=True)
    def load_data(self, internal_nodes, internal_edges, facilities):
        self.campus = load_graph_from_data(internal_nodes, internal_edges, "MAP_CAMPUS_001")
        self.scenic = load_graph_from_data(internal_nodes, internal_edges, "MAP_SCENIC_001")
        self.campus_facs = filter_by_map_id(facilities, "MAP_CAMPUS_001")
        self.scenic_facs = filter_by_map_id(facilities, "MAP_SCENIC_001")

    def test_returns_results(self):
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        results = calculate_nearby_facilities_by_road_distance(
            self.campus, start, self.campus_facs
        )
        assert len(results) > 0

    def test_road_distance_field(self):
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        results = calculate_nearby_facilities_by_road_distance(
            self.campus, start, self.campus_facs
        )
        for r in results:
            assert "road_distance" in r
            assert r["road_distance"] > 0

    def test_path_field(self):
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        results = calculate_nearby_facilities_by_road_distance(
            self.campus, start, self.campus_facs
        )
        for r in results:
            assert "path" in r
            assert len(r["path"]) >= 2

    def test_sorted_by_road_distance_asc(self):
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        results = calculate_nearby_facilities_by_road_distance(
            self.campus, start, self.campus_facs
        )
        distances = [r["road_distance"] for r in results]
        assert distances == sorted(distances)

    def test_category_filter(self):
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        results = calculate_nearby_facilities_by_road_distance(
            self.campus, start, self.campus_facs, category="toilet"
        )
        for r in results:
            assert r["category"] == "toilet"

    def test_keyword_filter(self):
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        results = calculate_nearby_facilities_by_road_distance(
            self.campus, start, self.campus_facs, keyword="超市"
        )
        assert len(results) > 0
        for r in results:
            has_keyword = (
                ("超市" in (r.get("name") or ""))
                or ("超市" in (r.get("category") or ""))
                or ("超市" in (r.get("description") or ""))
            )
            assert has_keyword

    def test_radius_filter(self):
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        all_results = calculate_nearby_facilities_by_road_distance(
            self.campus, start, self.campus_facs
        )
        if len(all_results) >= 2:
            cutoff = all_results[1]["road_distance"]
            limited = calculate_nearby_facilities_by_road_distance(
                self.campus, start, self.campus_facs, radius=cutoff
            )
            for r in limited:
                assert r["road_distance"] <= cutoff

    def test_no_straight_line_distance_in_results(self):
        """附近设施不应使用直线距离作为排序依据。"""
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        results = calculate_nearby_facilities_by_road_distance(
            self.campus, start, self.campus_facs
        )
        # 不应有 straight_distance 或 linear_distance 字段
        for r in results:
            assert "straight_distance" not in r
            assert "linear_distance" not in r
            # 排序用的是 road_distance
            assert "road_distance" in r

    def test_scenic_map(self):
        node_ids = list(self.scenic.nodes.keys())
        start = node_ids[0]
        results = calculate_nearby_facilities_by_road_distance(
            self.scenic, start, self.scenic_facs
        )
        # should work for scenic map too
        assert isinstance(results, list)


class TestValidateFacilities:
    def test_all_same_map(self):
        facs = [{"map_id": "M1"}, {"map_id": "M1"}]
        assert validate_facilities_same_map(facs, "M1") is True

    def test_mixed_map(self):
        facs = [{"map_id": "M1"}, {"map_id": "M2"}]
        assert validate_facilities_same_map(facs, "M1") is False


class TestExtractPathCoordinates:
    def test_extract(self):
        g = type('Graph', (), {
            'get_coordinates': lambda self, nid: {
                'A': [39.9, 116.3], 'B': [39.91, 116.31]
            }.get(nid)
        })()
        coords = extract_path_coordinates(g, ["A", "B", "C"])
        assert coords == [[39.9, 116.3], [39.91, 116.31]]
