"""
Dijkstra 最短路径算法测试
"""
import pytest
from backend.algorithms.graph import load_graph_from_data
from backend.algorithms.dijkstra import (
    dijkstra_shortest_distance,
    dijkstra_shortest_time,
    dijkstra_mixed_time,
    multi_point_route,
    dijkstra_all_distances,
    reconstruct_path_from_prev,
    reconstruct_segments_from_prev,
    calculate_edge_time,
    choose_best_transport_for_edge,
    INF,
)


class TestCalculateEdgeTime:
    def test_walk_allowed(self):
        edge = {
            "distance": 120,
            "congestion": 0.9,
            "ideal_speed_walk": 1.2,
            "allowed_transport": ["walk", "bike"],
        }
        result = calculate_edge_time(edge, "walk")
        assert result is not None
        assert result["transport"] == "walk"
        assert result["ideal_speed"] == 1.2
        assert result["real_speed"] == 0.9 * 1.2
        assert abs(result["time"] - 120 / (0.9 * 1.2)) < 0.001

    def test_transport_not_allowed(self):
        edge = {
            "distance": 100,
            "congestion": 1.0,
            "ideal_speed_walk": 1.2,
            "allowed_transport": ["walk"],
        }
        assert calculate_edge_time(edge, "bike") is None

    def test_speed_zero(self):
        edge = {
            "distance": 100,
            "congestion": 1.0,
            "ideal_speed_walk": 1.2,
            "ideal_speed_bike": 0,
            "allowed_transport": ["walk", "bike"],
        }
        assert calculate_edge_time(edge, "bike") is None


class TestChooseBestTransport:
    def test_campus_walk_or_bike(self):
        edge = {
            "distance": 200,
            "congestion": 0.8,
            "ideal_speed_walk": 1.2,
            "ideal_speed_bike": 4.0,
            "allowed_transport": ["walk", "bike"],
        }
        best = choose_best_transport_for_edge(edge, "campus")
        assert best is not None
        assert best["transport"] == "bike"  # bike is faster

    def test_attraction_no_bike(self):
        edge = {
            "distance": 200,
            "congestion": 0.8,
            "ideal_speed_walk": 1.2,
            "ideal_speed_bike": 4.0,
            "allowed_transport": ["walk", "bike"],
        }
        best = choose_best_transport_for_edge(edge, "attraction")
        # attraction has walk/sightseeing_car; bike not in candidates
        assert best["transport"] == "walk"

    def test_none_available(self):
        edge = {
            "distance": 100,
            "congestion": 1.0,
            "ideal_speed_walk": 1.2,
            "allowed_transport": ["sightseeing_car"],
        }
        # campus can't use sightseeing_car
        assert choose_best_transport_for_edge(edge, "campus") is None


class TestDijkstraRealData:
    @pytest.fixture(autouse=True)
    def load_graphs(self, internal_nodes, internal_edges):
        self.campus = load_graph_from_data(internal_nodes, internal_edges, "MAP_CAMPUS_001")
        self.scenic = load_graph_from_data(internal_nodes, internal_edges, "MAP_SCENIC_001")
        self.mixed = load_graph_from_data(internal_nodes, internal_edges, "MAP_MIXED_001")

    def _get_two_nodes(self, graph):
        """获取图中的前两个节点 ID。"""
        node_ids = list(graph.nodes.keys())
        assert len(node_ids) >= 2
        return node_ids[0], node_ids[1]

    # --- shortest_distance ---
    def test_shortest_distance_reachable(self):
        s, e = self._get_two_nodes(self.campus)
        result = dijkstra_shortest_distance(self.campus, s, e)
        assert result["reachable"] is True
        assert len(result["path"]) >= 2
        assert result["total_distance"] > 0

    def test_shortest_distance_segments(self):
        s, e = self._get_two_nodes(self.campus)
        result = dijkstra_shortest_distance(self.campus, s, e)
        assert len(result["segments"]) == len(result["path"]) - 1
        for seg in result["segments"]:
            assert "distance" in seg
            assert seg["distance"] > 0
            assert "from" in seg
            assert "to" in seg
            assert "from_name" in seg
            assert "to_name" in seg

    # --- shortest_time walk ---
    def test_shortest_time_walk_reachable(self):
        s, e = self._get_two_nodes(self.campus)
        result = dijkstra_shortest_time(self.campus, s, e, transport="walk")
        assert result["reachable"] is True
        assert result["total_time"] > 0

    def test_shortest_time_segments_have_congestion_and_speed(self):
        s, e = self._get_two_nodes(self.campus)
        result = dijkstra_shortest_time(self.campus, s, e, transport="walk")
        for seg in result["segments"]:
            assert "congestion" in seg
            assert seg["congestion"] is not None
            assert "ideal_speed" in seg
            assert seg["ideal_speed"] is not None
            assert "real_speed" in seg
            assert seg["real_speed"] is not None
            assert "time" in seg
            assert seg["time"] > 0

    # --- shortest_time bike / sightseeing_car ---
    def test_bike_in_campus(self):
        s, e = self._get_two_nodes(self.campus)
        result = dijkstra_shortest_time(self.campus, s, e, transport="bike")
        assert result["reachable"] is True
        # bike should be faster than walk on edges that allow both
        # at least some segments should use bike
        transports = {seg["transport"] for seg in result["segments"]}
        assert "bike" in transports

    def test_sightseeing_car_in_scenic(self):
        s, e = self._get_two_nodes(self.scenic)
        result = dijkstra_shortest_time(self.scenic, s, e, transport="sightseeing_car")
        # sightseeing may or may not reach all nodes; just check it runs
        assert "reachable" in result

    # --- mixed_time ---
    def test_mixed_time_campus(self):
        s, e = self._get_two_nodes(self.campus)
        result = dijkstra_mixed_time(self.campus, s, e, "campus")
        assert result["reachable"] is True
        # each segment should have a transport
        for seg in result["segments"]:
            assert seg["transport"] is not None
            assert seg["transport"] in ("walk", "bike")

    def test_mixed_time_scenic(self):
        s, e = self._get_two_nodes(self.scenic)
        result = dijkstra_mixed_time(self.scenic, s, e, "attraction")
        assert result["reachable"] is True
        for seg in result["segments"]:
            assert seg["transport"] in ("walk", "sightseeing_car")

    def test_mixed_time_mixed(self):
        s, e = self._get_two_nodes(self.mixed)
        result = dijkstra_mixed_time(self.mixed, s, e, "mixed")
        assert result["reachable"] is True

    # --- error handling ---
    def test_nonexistent_start(self):
        _, e = self._get_two_nodes(self.campus)
        with pytest.raises(ValueError, match="Start node not found"):
            dijkstra_shortest_distance(self.campus, "NONEXIST", e)

    def test_nonexistent_end(self):
        s, _ = self._get_two_nodes(self.campus)
        with pytest.raises(ValueError, match="End node not found"):
            dijkstra_shortest_distance(self.campus, s, "NONEXIST")

    # --- geometry ---
    def test_segments_contain_geometry(self):
        s, e = self._get_two_nodes(self.campus)
        result = dijkstra_shortest_distance(self.campus, s, e)
        for seg in result["segments"]:
            assert "geometry" in seg, "Segment missing geometry field"
            assert seg["geometry"] is not None
            assert len(seg["geometry"]) >= 2, f"Geometry has {len(seg['geometry'])} points"

    def test_extract_route_geometry(self):
        from backend.algorithms.dijkstra import extract_route_geometry
        s, e = self._get_two_nodes(self.campus)
        result = dijkstra_shortest_distance(self.campus, s, e)
        rg = extract_route_geometry(result["segments"])
        assert len(rg) >= 2
        for pt in rg:
            assert len(pt) == 2

    # --- same node ---
    def test_same_node(self):
        s, _ = self._get_two_nodes(self.campus)
        result = dijkstra_shortest_distance(self.campus, s, s)
        assert result["reachable"] is True
        assert result["path"] == [s]
        assert result["total_distance"] == 0


class TestMultiPointRoute:
    @pytest.fixture(autouse=True)
    def load_graphs(self, internal_nodes, internal_edges):
        self.campus = load_graph_from_data(internal_nodes, internal_edges, "MAP_CAMPUS_001")

    def test_multi_point_route(self):
        node_ids = list(self.campus.nodes.keys())
        start = node_ids[0]
        targets = node_ids[1:4]  # 3 targets
        result = multi_point_route(self.campus, start, targets, strategy="shortest_distance")
        assert result["reachable"] is True
        assert len(result["visit_order"]) == len(targets)
        assert result["total_distance"] > 0
        # should visit all targets
        for t in targets:
            assert t in result["visit_order"]

    def test_multi_point_empty_targets(self):
        node_ids = list(self.campus.nodes.keys())
        result = multi_point_route(self.campus, node_ids[0], [])
        assert result["reachable"] is True
        assert result["visit_order"] == []
        assert result["total_distance"] == 0


class TestDijkstraAllDistances:
    """单源全节点 Dijkstra 测试。"""

    @pytest.fixture(autouse=True)
    def load_graphs(self, internal_nodes, internal_edges):
        self.campus = load_graph_from_data(internal_nodes, internal_edges, "MAP_CAMPUS_001")

    def test_returns_all_nodes(self):
        s = list(self.campus.nodes.keys())[0]
        result = dijkstra_all_distances(self.campus, s)
        assert "dist" in result
        assert "prev" in result
        assert "prev_edge" in result
        assert len(result["dist"]) == self.campus.node_count()
        # start node distance is 0
        assert result["dist"][s] == 0
        assert result["prev"][s] is None

    def test_all_reachable_nodes_have_finite_distance(self):
        s = list(self.campus.nodes.keys())[0]
        result = dijkstra_all_distances(self.campus, s)
        reachable = sum(1 for d in result["dist"].values() if d < INF)
        # in a connected graph, most nodes should be reachable
        assert reachable >= 2

    def test_consistent_with_single_pair_dijkstra(self):
        """验证全节点距离与逐对 Dijkstra 结果一致。"""
        node_ids = list(self.campus.nodes.keys())
        s = node_ids[0]
        all_dist = dijkstra_all_distances(self.campus, s)

        for target in node_ids[1:]:
            single = dijkstra_shortest_distance(self.campus, s, target)
            if single["reachable"]:
                assert abs(all_dist["dist"][target] - single["total_distance"]) < 0.01, \
                    f"Distance mismatch for {target}"
            else:
                assert all_dist["dist"][target] == INF

    def test_reconstruct_path(self):
        node_ids = list(self.campus.nodes.keys())
        s, e = node_ids[0], node_ids[1]
        all_dist = dijkstra_all_distances(self.campus, s)
        path = reconstruct_path_from_prev(all_dist["prev"], s, e)
        assert len(path) >= 2
        assert path[0] == s
        assert path[-1] == e

    def test_reconstruct_path_same_node(self):
        node_ids = list(self.campus.nodes.keys())
        s = node_ids[0]
        all_dist = dijkstra_all_distances(self.campus, s)
        path = reconstruct_path_from_prev(all_dist["prev"], s, s)
        assert path == [s]

    def test_reconstruct_segments(self):
        node_ids = list(self.campus.nodes.keys())
        s, e = node_ids[0], node_ids[1]
        all_dist = dijkstra_all_distances(self.campus, s)
        result = reconstruct_segments_from_prev(
            self.campus, all_dist["prev"], all_dist["prev_edge"], s, e
        )
        assert len(result["segments"]) >= 1
        assert result["total_distance"] > 0
        assert len(result["path"]) == len(result["segments"]) + 1
        for seg in result["segments"]:
            assert "geometry" in seg
            assert seg["geometry"] is not None
            assert len(seg["geometry"]) >= 2

    def test_reconstruct_segments_same_node(self):
        node_ids = list(self.campus.nodes.keys())
        s = node_ids[0]
        all_dist = dijkstra_all_distances(self.campus, s)
        result = reconstruct_segments_from_prev(
            self.campus, all_dist["prev"], all_dist["prev_edge"], s, s
        )
        assert result["path"] == [s]
        assert result["segments"] == []
        assert result["total_distance"] == 0
        assert result["total_time"] == 0
