"""
PathPal 全局配置
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# JSON 数据文件路径
DESTINATIONS_FILE = DATA_DIR / "destinations.json"
INTERNAL_MAPS_FILE = DATA_DIR / "internal_maps.json"
INTERNAL_NODES_FILE = DATA_DIR / "internal_nodes.json"
INTERNAL_EDGES_FILE = DATA_DIR / "internal_edges.json"
FACILITIES_FILE = DATA_DIR / "facilities.json"
USERS_FILE = DATA_DIR / "users.json"
INDOOR_GRAPHS_FILE = DATA_DIR / "indoor_graphs.json"

# Flask 配置
DEBUG = True
HOST = "0.0.0.0"
PORT = 5000

# 默认值
DEFAULT_K = 10
DEFAULT_SORT_BY = "popularity"
