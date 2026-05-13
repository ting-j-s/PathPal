"""
PathPal 自定义邻接表图结构
"""
import json
from pathlib import Path


class Graph:
    """邻接表无向/有向图"""

    def __init__(self, map_id=None, directed=False):
        self.map_id = map_id
        self.directed = directed
        self.nodes = {}       # node_id -> node_data
        self.adjacency = {}   # node_id -> [edge_data, ...]
        self.edges = []       # all edge_data

    def add_node(self, node_id, node_data):
        self.nodes[node_id] = node_data
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []

    def add_edge(self, edge_data):
        f = edge_data["from"]
        t = edge_data["to"]
        self.edges.append(edge_data)
        if f not in self.adjacency:
            self.adjacency[f] = []
        self.adjacency[f].append(edge_data)
        if not self.directed:
            if t not in self.adjacency:
                self.adjacency[t] = []
            self.adjacency[t].append(edge_data)

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id):
        return self.adjacency.get(node_id, [])

    def get_edge(self, from_id, to_id):
        for e in self.adjacency.get(from_id, []):
            if e["to"] == to_id or (not self.directed and e["from"] == to_id):
                return e
        return None

    def has_node(self, node_id):
        return node_id in self.nodes

    def node_count(self):
        return len(self.nodes)

    def edge_count(self):
        return len(self.edges)

    def get_coordinates(self, node_id):
        node = self.nodes.get(node_id)
        if node is None:
            return None
        return [node.get("latitude"), node.get("longitude")]

    def get_node_name(self, node_id):
        node = self.nodes.get(node_id)
        if node is None:
            return None
        return node.get("name", node_id)


def load_graph_from_data(nodes, edges, map_id, directed=False):
    """
    从内存数据加载指定 map_id 的图。
    nodes: list of node dicts
    edges: list of edge dicts
    """
    graph = Graph(map_id=map_id, directed=directed)

    # 加载属于该 map_id 的节点
    for node in nodes:
        if node.get("map_id") == map_id:
            graph.add_node(node["id"], node)

    # 构建节点 ID 集合（用于快速校验）
    node_ids = set(graph.nodes.keys())

    # 记录已添加的边（无向边去重）
    seen = set()

    for edge in edges:
        if edge.get("map_id") != map_id:
            continue
        f = edge["from"]
        t = edge["to"]
        if f not in node_ids or t not in node_ids:
            continue

        if not directed:
            key = tuple(sorted([f, t]))
            if key in seen:
                continue
            seen.add(key)

        graph.add_edge(edge)

    return graph


def load_graph_from_files(nodes_file, edges_file, map_id, directed=False):
    """
    从 JSON 文件加载指定 map_id 的图。
    """
    with open(nodes_file, "r", encoding="utf-8") as f:
        nodes = json.load(f)
    with open(edges_file, "r", encoding="utf-8") as f:
        edges = json.load(f)
    return load_graph_from_data(nodes, edges, map_id, directed=directed)
