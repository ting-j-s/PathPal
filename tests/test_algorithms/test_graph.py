"""
Graph 数据结构测试
"""
import pytest
from backend.algorithms.graph import (
    Graph, load_graph_from_data, load_graph_from_files
)


class TestGraph:
    def test_create_graph(self):
        g = Graph(map_id="MAP_CAMPUS_001")
        assert g.map_id == "MAP_CAMPUS_001"
        assert g.directed is False
        assert g.node_count() == 0
        assert g.edge_count() == 0

    def test_add_node(self):
        g = Graph(map_id="test")
        g.add_node("N1", {"id": "N1", "name": "Test Node", "latitude": 39.9, "longitude": 116.3})
        assert g.has_node("N1")
        assert g.node_count() == 1
        assert g.get_node_name("N1") == "Test Node"

    def test_add_edge_undirected(self):
        g = Graph(map_id="test")
        g.add_node("N1", {"id": "N1"})
        g.add_node("N2", {"id": "N2"})
        edge = {
            "id": "E1", "from": "N1", "to": "N2", "distance": 100,
            "congestion": 0.9, "allowed_transport": ["walk"],
            "ideal_speed_walk": 1.2, "ideal_speed_bike": 4.0,
            "ideal_speed_sightseeing_car": 0, "road_type": "main_road",
        }
        g.add_edge(edge)
        assert g.edge_count() == 1
        # neighbors are accessible from both sides
        assert len(g.get_neighbors("N1")) == 1
        assert len(g.get_neighbors("N2")) == 1

    def test_get_coordinates(self):
        g = Graph(map_id="test")
        g.add_node("N1", {"id": "N1", "latitude": 39.9, "longitude": 116.3})
        coords = g.get_coordinates("N1")
        assert coords == [39.9, 116.3]

    def test_get_coordinates_none(self):
        g = Graph(map_id="test")
        g.add_node("N1", {"id": "N1"})
        assert g.get_coordinates("N1") == [None, None]
        assert g.get_coordinates("NONEXIST") is None

    def test_get_node_name_missing(self):
        g = Graph(map_id="test")
        g.add_node("N1", {"id": "N1"})
        assert g.get_node_name("N1") == "N1"  # fallback to id


class TestLoadGraphFromData:
    def test_load_campus_map(self, internal_nodes, internal_edges):
        g = load_graph_from_data(internal_nodes, internal_edges, "MAP_CAMPUS_001")
        assert g.map_id == "MAP_CAMPUS_001"
        assert g.node_count() > 0
        assert g.edge_count() > 0
        # all edge from/to nodes should exist
        for edge in g.edges:
            assert g.has_node(edge["from"])
            assert g.has_node(edge["to"])

    def test_load_all_maps(self, internal_nodes, internal_edges):
        for map_id in ["MAP_CAMPUS_001", "MAP_SCENIC_001", "MAP_MIXED_001"]:
            g = load_graph_from_data(internal_nodes, internal_edges, map_id)
            assert g.node_count() > 0, f"{map_id} has 0 nodes"
            assert g.edge_count() > 0, f"{map_id} has 0 edges"

    def test_get_neighbors_returns_edges(self, internal_nodes, internal_edges):
        g = load_graph_from_data(internal_nodes, internal_edges, "MAP_CAMPUS_001")
        node_ids = list(g.nodes.keys())
        if len(node_ids) > 1:
            neighbors = g.get_neighbors(node_ids[0])
            assert isinstance(neighbors, list)

    def test_graph_undirected_no_duplicate_edges(self, internal_nodes, internal_edges):
        g = load_graph_from_data(internal_nodes, internal_edges, "MAP_CAMPUS_001")
        edge_pairs = set()
        for edge in g.edges:
            key = tuple(sorted([edge["from"], edge["to"]]))
            assert key not in edge_pairs, f"Duplicate edge: {key}"
            edge_pairs.add(key)

    def test_load_nonexistent_map(self, internal_nodes, internal_edges):
        g = load_graph_from_data(internal_nodes, internal_edges, "MAP_NONEXIST")
        assert g.node_count() == 0
        assert g.edge_count() == 0

    def test_null_edge(self, internal_nodes, internal_edges):
        """edge with from/to not in nodes should be skipped."""
        nodes = [{"id": "N1", "map_id": "T1"}, {"id": "N2", "map_id": "T1"}]
        edges = [
            {"id": "E1", "map_id": "T1", "from": "N1", "to": "N2", "distance": 100,
             "congestion": 1.0, "allowed_transport": ["walk"],
             "ideal_speed_walk": 1.2, "ideal_speed_bike": 4.0,
             "ideal_speed_sightseeing_car": 0, "road_type": "path"},
            {"id": "E2", "map_id": "T1", "from": "N1", "to": "N3", "distance": 50,
             "congestion": 1.0, "allowed_transport": ["walk"],
             "ideal_speed_walk": 1.2, "ideal_speed_bike": 4.0,
             "ideal_speed_sightseeing_car": 0, "road_type": "path"},
        ]
        g = load_graph_from_data(nodes, edges, "T1")
        assert g.edge_count() == 1
