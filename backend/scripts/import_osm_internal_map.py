#!/usr/bin/env python3
"""
PathPal OSM 矢量数据导入脚本
从 Overpass API 获取指定区域的 OSM 道路矢量数据，转换为 PathPal 内部图数据。

支持的导入目标：
  - MAP_BUPT_REAL: 北京邮电大学校园
  - MAP_SCENIC_REAL: 天坛公园

Usage:
  python backend/scripts/import_osm_internal_map.py
"""
import json
import math
import random
import ssl
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# ============================================================
# 配置
# ============================================================

R = 6371000  # 地球半径（米）

IMPORT_CONFIGS = {
    "MAP_BUPT_REAL": {
        "name": "北京邮电大学 OSM 矢量校园内部图",
        "type": "campus",
        "destination_id": "DEST_001",
        "destination_name": "北京邮电大学",
        "bbox": {
            "lat_min": 39.9500, "lat_max": 39.9720,
            "lng_min": 116.3440, "lng_max": 116.3690,
        },
        "default_zoom": 17,
        "supported_transports": ["walk", "bike"],
        "highway_types": ["footway", "path", "pedestrian", "service",
                          "cycleway", "living_street", "steps",
                          "tertiary", "residential", "unclassified"],
        "transport_default": ["walk"],
        "transport_extended": ["walk", "bike"],
        "extended_types": {"cycleway", "service", "living_street",
                           "tertiary", "residential", "unclassified"},
        "forbidden_transport": "sightseeing_car",
        "ideal_speed_walk": 80,
        "ideal_speed_bike": 220,
        "ideal_speed_sightseeing_car": None,
        "node_prefix": "NODE_BUPT_OSM",
        "edge_prefix": "EDGE_BUPT_OSM",
        "semantic_pois": [
            {"id": "POI_BUPT_001", "name": "北邮北门", "type": "gate",
             "lat": 39.9636, "lng": 116.3575},
            {"id": "POI_BUPT_002", "name": "北邮南门", "type": "gate",
             "lat": 39.9589, "lng": 116.3573},
            {"id": "POI_BUPT_003", "name": "北邮西门", "type": "gate",
             "lat": 39.9615, "lng": 116.3542},
            {"id": "POI_BUPT_004", "name": "北邮东门", "type": "gate",
             "lat": 39.9615, "lng": 116.3578},
            {"id": "POI_BUPT_005", "name": "图书馆", "type": "building",
             "lat": 39.9622, "lng": 116.3563},
            {"id": "POI_BUPT_006", "name": "主楼", "type": "building",
             "lat": 39.96295, "lng": 116.35705},
            {"id": "POI_BUPT_007", "name": "教学楼(教三楼)", "type": "building",
             "lat": 39.96195, "lng": 116.35705},
            {"id": "POI_BUPT_008", "name": "科研楼", "type": "building",
             "lat": 39.9605, "lng": 116.3558},
            {"id": "POI_BUPT_009", "name": "体育馆", "type": "building",
             "lat": 39.9592, "lng": 116.3560},
            {"id": "POI_BUPT_010", "name": "操场", "type": "scenic_spot",
             "lat": 39.9595, "lng": 116.3555},
            {"id": "POI_BUPT_011", "name": "学生活动中心", "type": "building",
             "lat": 39.9610, "lng": 116.3560},
            {"id": "POI_BUPT_012", "name": "学生公寓区", "type": "building",
             "lat": 39.9590, "lng": 116.3571},
            {"id": "POI_BUPT_013", "name": "食堂", "type": "building",
             "lat": 39.9604, "lng": 116.3568},
        ],
        "facilities": [
            {"id": "FAC_BUPT_OSM_001", "name": "图书馆咖啡厅", "category": "cafe",
             "poi_id": "POI_BUPT_005", "description": "图书馆一楼咖啡厅"},
            {"id": "FAC_BUPT_OSM_002", "name": "主楼洗手间(1F)", "category": "toilet",
             "poi_id": "POI_BUPT_006", "description": "主楼一层公共洗手间"},
            {"id": "FAC_BUPT_OSM_003", "name": "教三楼洗手间(1F)", "category": "toilet",
             "poi_id": "POI_BUPT_007", "description": "教三楼一层洗手间"},
            {"id": "FAC_BUPT_OSM_004", "name": "食堂", "category": "canteen",
             "poi_id": "POI_BUPT_013", "description": "学生食堂"},
            {"id": "FAC_BUPT_OSM_005", "name": "校园超市", "category": "supermarket",
             "poi_id": "POI_BUPT_012", "description": "学生公寓区便利店"},
            {"id": "FAC_BUPT_OSM_006", "name": "图书馆", "category": "library",
             "poi_id": "POI_BUPT_005", "description": "北京邮电大学图书馆"},
            {"id": "FAC_BUPT_OSM_007", "name": "体育场洗手间", "category": "toilet",
             "poi_id": "POI_BUPT_010", "description": "操场旁公共洗手间"},
            {"id": "FAC_BUPT_OSM_008", "name": "北门门卫室", "category": "service_desk",
             "poi_id": "POI_BUPT_001", "description": "北门访客登记处"},
            {"id": "FAC_BUPT_OSM_009", "name": "南门服务点", "category": "service_desk",
             "poi_id": "POI_BUPT_002", "description": "南门服务咨询"},
            {"id": "FAC_BUPT_OSM_010", "name": "体育馆服务台", "category": "service_desk",
             "poi_id": "POI_BUPT_009", "description": "体育馆前台"},
            {"id": "FAC_BUPT_OSM_011", "name": "教学楼咖啡点", "category": "cafe",
             "poi_id": "POI_BUPT_007", "description": "教三楼自动咖啡机"},
            {"id": "FAC_BUPT_OSM_012", "name": "食堂洗手间", "category": "toilet",
             "poi_id": "POI_BUPT_013", "description": "食堂旁洗手间"},
            {"id": "FAC_BUPT_OSM_013", "name": "科研楼超市", "category": "shop",
             "poi_id": "POI_BUPT_008", "description": "科研楼小卖部"},
            {"id": "FAC_BUPT_OSM_014", "name": "活动中心洗手间", "category": "toilet",
             "poi_id": "POI_BUPT_011", "description": "学生活动中心洗手间"},
            {"id": "FAC_BUPT_OSM_015", "name": "西门快递站", "category": "service_desk",
             "poi_id": "POI_BUPT_003", "description": "西门快递收发点"},
        ],
    },
    "MAP_SCENIC_REAL": {
        "name": "天坛公园 OSM 矢量内部图",
        "type": "attraction",
        "destination_id": "DEST_032",
        "destination_name": "天坛公园",
        "bbox": {
            "lat_min": 39.8600, "lat_max": 39.9070,
            "lng_min": 116.3800, "lng_max": 116.4380,
        },
        "default_zoom": 16,
        "supported_transports": ["walk", "sightseeing_car"],
        "highway_types": ["footway", "path", "pedestrian", "steps"],
        "transport_default": ["walk"],
        "transport_extended": ["walk", "sightseeing_car"],
        "extended_types": {"pedestrian"},
        "forbidden_transport": "bike",
        "ideal_speed_walk": 70,
        "ideal_speed_bike": None,
        "ideal_speed_sightseeing_car": 300,
        "node_prefix": "NODE_TIANTAN_OSM",
        "edge_prefix": "EDGE_TIANTAN_OSM",
        "semantic_pois": [
            {"id": "POI_TSR_001", "name": "天坛南门", "type": "gate",
             "lat": 39.8760, "lng": 116.4066},
            {"id": "POI_TSR_002", "name": "天坛北门", "type": "gate",
             "lat": 39.8890, "lng": 116.4066},
            {"id": "POI_TSR_003", "name": "天坛东门", "type": "gate",
             "lat": 39.8822, "lng": 116.4110},
            {"id": "POI_TSR_004", "name": "天坛西门", "type": "gate",
             "lat": 39.8822, "lng": 116.4022},
            {"id": "POI_TSR_005", "name": "祈年殿", "type": "scenic_spot",
             "lat": 39.8855, "lng": 116.4066},
            {"id": "POI_TSR_006", "name": "回音壁", "type": "scenic_spot",
             "lat": 39.8832, "lng": 116.4072},
            {"id": "POI_TSR_007", "name": "圜丘", "type": "scenic_spot",
             "lat": 39.8800, "lng": 116.4066},
            {"id": "POI_TSR_008", "name": "丹陛桥", "type": "scenic_spot",
             "lat": 39.8825, "lng": 116.4066},
            {"id": "POI_TSR_009", "name": "斋宫", "type": "scenic_spot",
             "lat": 39.8810, "lng": 116.4040},
            {"id": "POI_TSR_010", "name": "游客服务中心", "type": "building",
             "lat": 39.8875, "lng": 116.4063},
        ],
        "facilities": [
            {"id": "FAC_TSR_OSM_001", "name": "游客服务中心", "category": "service_desk",
             "poi_id": "POI_TSR_010", "description": "旅游咨询、导览图、轮椅租赁"},
            {"id": "FAC_TSR_OSM_002", "name": "北门洗手间", "category": "toilet",
             "poi_id": "POI_TSR_002", "description": "北门附近公共洗手间"},
            {"id": "FAC_TSR_OSM_003", "name": "南门洗手间", "category": "toilet",
             "poi_id": "POI_TSR_001", "description": "南门附近公共洗手间"},
            {"id": "FAC_TSR_OSM_004", "name": "东门洗手间", "category": "toilet",
             "poi_id": "POI_TSR_003", "description": "东门附近公共洗手间"},
            {"id": "FAC_TSR_OSM_005", "name": "西门洗手间", "category": "toilet",
             "poi_id": "POI_TSR_004", "description": "西门附近公共洗手间"},
            {"id": "FAC_TSR_OSM_006", "name": "祈年殿文创商店", "category": "shop",
             "poi_id": "POI_TSR_005", "description": "天坛主题文创纪念品"},
            {"id": "FAC_TSR_OSM_007", "name": "回音壁咖啡点", "category": "cafe",
             "poi_id": "POI_TSR_006", "description": "景区自动咖啡售卖"},
            {"id": "FAC_TSR_OSM_008", "name": "圜丘售票处", "category": "ticket",
             "poi_id": "POI_TSR_007", "description": "圜丘景区入口售票"},
            {"id": "FAC_TSR_OSM_009", "name": "丹陛桥休息点", "category": "restaurant",
             "poi_id": "POI_TSR_008", "description": "中轴线休息区"},
            {"id": "FAC_TSR_OSM_010", "name": "斋宫洗手间", "category": "toilet",
             "poi_id": "POI_TSR_009", "description": "斋宫景区洗手间"},
            {"id": "FAC_TSR_OSM_011", "name": "祈年殿洗手间", "category": "toilet",
             "poi_id": "POI_TSR_005", "description": "祈年殿附近洗手间"},
            {"id": "FAC_TSR_OSM_012", "name": "北门售票处", "category": "ticket",
             "poi_id": "POI_TSR_002", "description": "北门入口售票处"},
            {"id": "FAC_TSR_OSM_013", "name": "南门售票处", "category": "ticket",
             "poi_id": "POI_TSR_001", "description": "南门入口售票处"},
            {"id": "FAC_TSR_OSM_014", "name": "游客中心咖啡", "category": "cafe",
             "poi_id": "POI_TSR_010", "description": "游客服务中心咖啡吧"},
            {"id": "FAC_TSR_OSM_015", "name": "东门服务点", "category": "service_desk",
             "poi_id": "POI_TSR_003", "description": "东门游客服务点"},
        ],
    },
}


# ============================================================
# 工具函数
# ============================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """计算两点间 Haversine 距离，单位米。"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def node_in_bbox(n, bbox):
    """检查节点是否在 bbox 内（允许小范围溢出）。"""
    lat = n.get("lat", n.get("latitude", 0))
    lon = n.get("lon", n.get("longitude", 0))
    margin = 0.0005  # ~50m margin
    return (bbox["lat_min"] - margin <= lat <= bbox["lat_max"] + margin and
            bbox["lng_min"] - margin <= lon <= bbox["lng_max"] + margin)


def _overpass_request(query, timeout=95):
    """发送 Overpass API 请求并返回解析后的 JSON。"""
    req = urllib.request.Request(
        'https://overpass-api.de/api/interpreter',
        data=query.encode('utf-8'),
        headers={
            'Content-Type': 'text/plain',
            'User-Agent': 'PathPal/1.0 (educational project; data import)',
            'Accept': 'application/json',
        }
    )
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
    return json.loads(resp.read())


def query_overpass(bbox, highway_types):
    """从 Overpass API 获取道路、建筑及各类 POI 数据。
    分多次查询以避免城市密集区域超时。
    """
    bbox_str = f"{bbox['lat_min']},{bbox['lng_min']},{bbox['lat_max']},{bbox['lng_max']}"

    way_queries = "\n  ".join(
        f'way["highway"="{ht}"]({bbox_str});' for ht in highway_types
    )

    # 查询 1: 道路 ways
    query_roads = (
        f'[out:json][timeout:90];\n'
        f'(\n'
        f'  {way_queries}\n'
        f');\n'
        f'out body;\n'
        f'>;\n'
        f'out body;'
    )

    # 查询 2: 建筑 ways
    query_buildings = (
        f'[out:json][timeout:90];\n'
        f'(\n'
        f'  way["building"]({bbox_str});\n'
        f');\n'
        f'out body;\n'
        f'>;\n'
        f'out body;'
    )

    # 查询 3: POI 节点（命名 + 各类设施）
    query_pois = (
        f'[out:json][timeout:90];\n'
        f'(\n'
        f'  node["name"]({bbox_str});\n'
        f'  node["amenity"]({bbox_str});\n'
        f'  node["shop"]({bbox_str});\n'
        f'  node["tourism"]({bbox_str});\n'
        f'  node["leisure"]({bbox_str});\n'
        f'  node["office"]({bbox_str});\n'
        f');\n'
        f'out body;'
    )

    # 发送查询
    print(f"    查询 1/3: 道路...")
    result_roads = _overpass_request(query_roads, timeout=95)
    print(f"    查询 2/3: 建筑...")
    result_buildings = _overpass_request(query_buildings, timeout=95)
    print(f"    查询 3/3: POI 节点...")
    result_pois = _overpass_request(query_pois, timeout=95)

    # 合并结果
    all_elements = result_roads['elements'] + result_buildings['elements'] + result_pois['elements']

    road_ways = [e for e in all_elements if e['type'] == 'way' and 'highway' in e.get('tags', {})]
    building_ways = [e for e in all_elements if e['type'] == 'way' and 'building' in e.get('tags', {})]
    nodes_dict = {}
    for e in all_elements:
        if e['type'] == 'node':
            eid = e['id']
            if eid in nodes_dict:
                existing = nodes_dict[eid]
                if 'tags' in e and 'tags' not in existing:
                    existing['tags'] = e['tags']
                elif 'tags' in e and 'tags' in existing:
                    existing['tags'].update(e['tags'])
            else:
                nodes_dict[eid] = e

    return road_ways, building_ways, nodes_dict


def find_nearest_node(poi_lat, poi_lng, node_list):
    """找到距离 POI 最近的道路节点。"""
    best_node = None
    best_dist = float('inf')
    for node in node_list:
        d = haversine_distance(poi_lat, poi_lng, node["latitude"], node["longitude"])
        if d < best_dist:
            best_dist = d
            best_node = node
    return best_node, best_dist


# ============================================================
# 主导入逻辑
# ============================================================

def process_osm_data(ways, nodes_dict, map_id, config):
    """
    将 OSM way/node 转换为 PathPal 内部图数据。

    返回: (new_nodes, new_edges, node_counter, edge_counter)
    """
    bbox = config["bbox"]
    transport_default = config["transport_default"]
    transport_extended = config["transport_extended"]
    extended_types = config["extended_types"]
    node_prefix = config["node_prefix"]
    edge_prefix = config["edge_prefix"]
    ideal_speed_walk = config["ideal_speed_walk"]
    ideal_speed_bike = config.get("ideal_speed_bike")
    ideal_speed_sc = config.get("ideal_speed_sightseeing_car")

    # 收集所有 OSM node 及其坐标
    osm_node_coords = {}
    for nid, nd in nodes_dict.items():
        osm_node_coords[nid] = (nd["lat"], nd["lon"])

    # 过滤 bbox 内的节点
    bbox_nodes = set()
    for nid, (lat, lon) in osm_node_coords.items():
        if node_in_bbox({"lat": lat, "lon": lon}, bbox):
            bbox_nodes.add(nid)
    print(f"    OSM nodes in bbox: {len(bbox_nodes)}/{len(nodes_dict)}")

    # 收集所有使用到的 bbox 内节点
    used_nodes = set()
    processed_ways = []

    for way in ways:
        w_nodes = way.get("nodes", [])
        tags = way.get("tags", {})
        highway = tags.get("highway", "")
        oneway = tags.get("oneway", "no")

        # 过滤：只保留至少有一个节点在 bbox 内的 way
        way_bbox_nodes = [nid for nid in w_nodes if nid in bbox_nodes]
        if len(way_bbox_nodes) < 2:
            continue

        # 只保留 way 中的 bbox 内节点（连续段）
        # 找到连续的 bbox 内节点段
        segments = []
        current_seg = []
        for nid in w_nodes:
            if nid in bbox_nodes:
                current_seg.append(nid)
            else:
                if len(current_seg) >= 2:
                    segments.append(current_seg)
                current_seg = []
        if len(current_seg) >= 2:
            segments.append(current_seg)

        for seg in segments:
            processed_ways.append({
                "osm_way_id": way["id"],
                "highway": highway,
                "name": tags.get("name", ""),
                "oneway": oneway,
                "nodes": seg,
            })
            used_nodes.update(seg)

    print(f"    Processed OSM ways: {len(processed_ways)} (filtered from {len(ways)})")

    # 收集独立命名节点（未在任何 way 中使用）
    standalone_named = {}
    standalone_tagged = {}  # amenity/shop/tourism/leisure/office 节点（可无名）
    for nid, nd in nodes_dict.items():
        if nid not in used_nodes and nid in bbox_nodes:
            tags = nd.get("tags", {})
            name = tags.get("name", "") or tags.get("name:zh", "")
            if name:
                standalone_named[nid] = nd
            elif any(k in tags for k in ("amenity", "shop", "tourism", "leisure", "office")):
                standalone_tagged[nid] = nd
    print(f"    Standalone named POI nodes: {len(standalone_named)}")
    print(f"    Standalone tagged (unnamed) nodes: {len(standalone_tagged)}")

    # OSM 节点类型推断
    def _osm_node_type(tags):
        if tags.get("barrier") == "gate":
            return "gate"
        if tags.get("tourism") in ("artwork", "attraction"):
            return "scenic_spot"
        if tags.get("historic") == "memorial":
            return "scenic_spot"
        if tags.get("amenity") or tags.get("shop") or tags.get("office"):
            return "building"
        if tags.get("highway") == "bus_stop":
            return "intersection"
        if tags.get("public_transport") == "platform":
            return "intersection"
        return "intersection"

    def _osm_node_subtype(tags):
        if tags.get("barrier") == "gate":
            return "gate"
        if tags.get("tourism") == "artwork":
            return "artwork"
        if tags.get("historic") == "memorial":
            return "landmark"
        return "junction"

    # 创建 PathPal 节点
    osm_to_pathpal = {}
    new_nodes = []
    random.seed(42)

    node_counter = 0
    for osm_nid in sorted(used_nodes):
        lat, lon = osm_node_coords[osm_nid]
        nd = nodes_dict.get(osm_nid, {})
        tags = nd.get("tags", {})
        pp_id = f"{node_prefix}_{node_counter:06d}"
        node_counter += 1
        osm_to_pathpal[osm_nid] = pp_id

        # 优先使用 OSM 节点自身的名称
        osm_name = tags.get("name", "") or tags.get("name:zh", "")
        node_name = osm_name if osm_name else f"OSM节点-{osm_nid}"

        new_nodes.append({
            "id": pp_id,
            "map_id": map_id,
            "name": node_name,
            "type": _osm_node_type(tags) if osm_name else "intersection",
            "subtype": _osm_node_subtype(tags) if osm_name else "junction",
            "latitude": round(lat, 7),
            "longitude": round(lon, 7),
        })

    print(f"    PathPal nodes: {len(new_nodes)}")

    # 创建 PathPal 边
    new_edges = []
    edge_counter = 0

    for pw in processed_ways:
        highway = pw["highway"]
        seg_nodes = pw["nodes"]
        oneway = pw["oneway"]

        # 确定 transport
        if highway in extended_types:
            allowed_transport = list(transport_extended)
        else:
            allowed_transport = list(transport_default)

        for i in range(len(seg_nodes) - 1):
            n1_osm = seg_nodes[i]
            n2_osm = seg_nodes[i + 1]
            pp_from = osm_to_pathpal[n1_osm]
            pp_to = osm_to_pathpal[n2_osm]

            lat1, lon1 = osm_node_coords[n1_osm]
            lat2, lon2 = osm_node_coords[n2_osm]

            dist = haversine_distance(lat1, lon1, lat2, lon2)
            if dist < 0.1:  # 跳过几乎重合的节点
                continue

            congestion = round(random.uniform(0.65, 1.0), 2)
            geometry = [[lat1, lon1], [lat2, lon2]]

            edge = {
                "id": f"{edge_prefix}_{edge_counter:06d}",
                "map_id": map_id,
                "from": pp_from,
                "to": pp_to,
                "name": pw.get("name", ""),
                "distance": round(dist, 1),
                "congestion": congestion,
                "ideal_speed_walk": ideal_speed_walk / 60.0,
                "ideal_speed_bike": (ideal_speed_bike / 60.0) if ideal_speed_bike else 0,
                "ideal_speed_sightseeing_car": (ideal_speed_sc / 60.0) if ideal_speed_sc else 0,
                "allowed_transport": allowed_transport,
                "road_type": "main_road" if highway in ("pedestrian", "service", "tertiary", "residential", "unclassified") else "path",
                "geometry": geometry,
            }
            new_edges.append(edge)
            edge_counter += 1

            # 双向边（除非 oneway）
            if oneway != "yes":
                rev_edge = dict(edge)
                rev_edge["id"] = f"{edge_prefix}_{edge_counter:06d}"
                rev_edge["from"] = pp_to
                rev_edge["to"] = pp_from
                rev_edge["geometry"] = [[lat2, lon2], [lat1, lon1]]
                new_edges.append(rev_edge)
                edge_counter += 1

    print(f"    PathPal edges: {len(new_edges)}")

    return new_nodes, new_edges, node_counter, edge_counter, standalone_named, standalone_tagged


def create_named_node_pois(standalone_named, road_nodes, nodes_dict, map_id, config,
                           standalone_tagged=None):
    """
    为未在任何 way 上的 OSM 节点创建 POI 节点和连接边。
    standalone_named: {osm_nid: osm_node_element} 有名称的节点
    standalone_tagged: {osm_nid: osm_node_element} 有 amenity/shop 等标签但无名称
    """
    if not standalone_named and not standalone_tagged:
        return [], []

    node_prefix = config["node_prefix"]
    edge_prefix = config["edge_prefix"]
    transport_default = config["transport_default"]
    ideal_speed_walk = config["ideal_speed_walk"]

    poi_nodes = []
    poi_edges = []
    node_idx = 200000
    all_existing_names = {n["name"] for n in road_nodes}

    def _tag_to_name(tags):
        """为无名但有标签的节点生成名称。"""
        amenity = tags.get("amenity", "")
        shop = tags.get("shop", "")
        tourism = tags.get("tourism", "")
        leisure = tags.get("leisure", "")
        office = tags.get("office", "")
        if amenity:
            return f"{amenity}_{node_idx}"
        if shop:
            return f"{shop}_{node_idx}"
        if tourism:
            return f"{tourism}_{node_idx}"
        if leisure:
            return f"{leisure}_{node_idx}"
        if office:
            return f"{office}_{node_idx}"
        return None

    def _node_type_and_subtype(tags):
        if tags.get("barrier") == "gate":
            return "gate", "gate"
        if tags.get("tourism") in ("artwork", "attraction", "museum", "gallery"):
            return "scenic_spot", "attraction"
        if tags.get("historic"):
            return "scenic_spot", "landmark"
        if tags.get("amenity") in ("restaurant", "cafe", "fast_food", "bar", "pub", "food_court"):
            return "building", "restaurant"
        if tags.get("amenity") in ("bank", "post_office", "hospital", "pharmacy", "clinic", "atm"):
            return "building", "service"
        if tags.get("amenity") in ("library", "university", "college", "school"):
            return "building", "education"
        if tags.get("amenity") in ("parking", "bicycle_parking"):
            return "building", "parking"
        if tags.get("amenity") == "place_of_worship":
            return "building", "religious"
        if tags.get("amenity") in ("toilets", "toilet"):
            return "building", "toilet"
        if tags.get("shop"):
            return "building", "shop"
        if tags.get("office"):
            return "building", "office"
        if tags.get("leisure"):
            return "building", "leisure"
        if tags.get("tourism"):
            return "scenic_spot", "attraction"
        if tags.get("amenity"):
            return "building", "amenity"
        return "building", "poi"

    # 合并所有待处理节点
    all_standalone = {}
    for nid, nd in standalone_named.items():
        all_standalone[nid] = nd
    if standalone_tagged:
        for nid, nd in standalone_tagged.items():
            if nid not in all_standalone:
                all_standalone[nid] = nd

    for osm_nid, nd in all_standalone.items():
        tags = nd.get("tags", {})
        name = tags.get("name", "") or tags.get("name:zh", "")

        # 过滤：跳过纯公交站 / 交通信号 / 地铁站等非 POI 节点
        if tags.get("highway") in ("bus_stop", "traffic_signals", "crossing", "stop"):
            continue
        if tags.get("public_transport") in ("stop_position", "platform", "station"):
            continue
        if tags.get("railway") in ("stop", "subway_entrance"):
            continue
        if tags.get("barrier") in ("gate", "bollard") and not name:
            continue

        lat = nd.get("lat", 0)
        lon = nd.get("lon", 0)

        ntype, subtype = _node_type_and_subtype(tags)

        # 过滤：跳过纯 bench / waste_basket / lamp 等微小设施（除非 bbox 内且靠近道路）
        if not name and tags.get("amenity") in ("bench", "waste_basket", "waste_disposal",
                                                  "recycling", "lamp_post", "street_lamp",
                                                  "fountain", "drinking_water"):
            continue
        if not name and tags.get("man_made") in ("manhole", "drain", "utility_pole"):
            continue

        # 无名称节点生成名称
        if not name:
            name = _tag_to_name(tags)
            if not name:
                continue

        # 找到最近的道路节点
        nearest, min_dist = None, float('inf')
        for rn in road_nodes:
            d = haversine_distance(lat, lon, rn["latitude"], rn["longitude"])
            if d < min_dist:
                min_dist = d
                nearest = rn

        max_dist = 300 if name and not name.startswith(("bench", "waste")) else 200
        if nearest is None or min_dist > max_dist:
            continue

        # 创建 POI 节点
        if name in all_existing_names:
            name = f"{name}_{node_idx}"
        all_existing_names.add(name)

        poi_id = f"{node_prefix}_POI_{node_idx:06d}"
        node_idx += 1
        poi_node = {
            "id": poi_id,
            "map_id": map_id,
            "name": name,
            "type": ntype,
            "subtype": subtype,
            "latitude": round(lat, 7),
            "longitude": round(lon, 7),
        }
        poi_nodes.append(poi_node)

        # 创建双向连接边
        dist = max(min_dist, 0.1)
        edge_a = {
            "id": f"{edge_prefix}_POI_{node_idx:06d}",
            "map_id": map_id,
            "from": poi_id,
            "to": nearest["id"],
            "name": "",
            "distance": round(dist, 1),
            "congestion": 0.9,
            "ideal_speed_walk": ideal_speed_walk / 60.0,
            "ideal_speed_bike": 0,
            "ideal_speed_sightseeing_car": 0,
            "allowed_transport": list(transport_default),
            "road_type": "path",
            "geometry": [[lat, lon], [nearest["latitude"], nearest["longitude"]]],
        }
        poi_edges.append(edge_a)
        node_idx += 1

        edge_b = dict(edge_a)
        edge_b["id"] = f"{edge_prefix}_POI_{node_idx:06d}"
        edge_b["from"] = nearest["id"]
        edge_b["to"] = poi_id
        edge_b["geometry"] = [[nearest["latitude"], nearest["longitude"]], [lat, lon]]
        poi_edges.append(edge_b)
        node_idx += 1

    print(f"    OSM POI nodes: {len(poi_nodes)}, connection edges: {len(poi_edges)}")
    return poi_nodes, poi_edges


def process_building_ways(building_ways, nodes_dict, road_nodes, map_id, config):
    """
    将 OSM 建筑轮廓转换为 POI 节点（取中心点）。
    只保留有名称或有意义标签的建筑。
    """
    if not building_ways:
        return [], []

    bbox = config["bbox"]
    node_prefix = config["node_prefix"]
    edge_prefix = config["edge_prefix"]
    transport_default = config["transport_default"]
    ideal_speed_walk = config["ideal_speed_walk"]

    poi_nodes = []
    poi_edges = []
    node_idx = 300000

    def _building_name_and_type(tags):
        """从 building 标签提取名称和类型。"""
        name = tags.get("name", "") or tags.get("name:zh", "") or tags.get("official_name", "")
        if not name:
            name = tags.get("operator", "")

        # 确定类型
        if tags.get("tourism") in ("museum", "attraction", "artwork", "gallery"):
            ntype, subtype = "scenic_spot", "attraction"
        elif tags.get("historic"):
            ntype, subtype = "scenic_spot", "landmark"
        elif tags.get("amenity") in ("university", "college", "school"):
            ntype, subtype = "building", "education"
        elif tags.get("amenity") == "library":
            ntype, subtype = "building", "library"
        elif tags.get("amenity") in ("restaurant", "cafe", "fast_food", "bar", "pub"):
            ntype, subtype = "building", "restaurant"
        elif tags.get("amenity") in ("bank", "post_office", "hospital", "pharmacy", "clinic"):
            ntype, subtype = "building", "service"
        elif tags.get("shop"):
            ntype, subtype = "building", "shop"
        elif tags.get("office"):
            ntype, subtype = "building", "office"
        elif tags.get("leisure") in ("sports_centre", "fitness_centre", "stadium"):
            ntype, subtype = "building", "sports"
        elif tags.get("building") in ("dormitory", "dorm"):
            ntype, subtype = "building", "dormitory"
        elif tags.get("building") in ("civic", "government", "public"):
            ntype, subtype = "building", "civic"
        elif tags.get("amenity") == "place_of_worship":
            ntype, subtype = "building", "religious"
        elif tags.get("amenity") == "parking":
            ntype, subtype = "building", "parking"
        elif name:
            ntype, subtype = "building", "building"
        else:
            ntype, subtype = None, None  # 无名称且无意义标签 → 跳过

        return name, ntype, subtype

    for bw in building_ways:
        tags = bw.get("tags", {})
        name, ntype, subtype = _building_name_and_type(tags)
        if not name and not ntype:
            continue  # 跳过无名且无意义的建筑

        w_nodes = bw.get("nodes", [])
        if len(w_nodes) < 2:
            continue

        # 计算建筑中心点
        lats, lngs = [], []
        for nid in w_nodes:
            nd = nodes_dict.get(nid)
            if nd:
                lats.append(nd["lat"])
                lngs.append(nd["lon"])

        if len(lats) < 2:
            continue

        center_lat = round(sum(lats) / len(lats), 7)
        center_lng = round(sum(lngs) / len(lngs), 7)

        # 检查是否在 bbox 内
        margin = 0.001
        if not (bbox["lat_min"] - margin <= center_lat <= bbox["lat_max"] + margin and
                bbox["lng_min"] - margin <= center_lng <= bbox["lng_max"] + margin):
            continue

        # 找到最近的道路节点
        nearest, min_dist = None, float('inf')
        for rn in road_nodes:
            d = haversine_distance(center_lat, center_lng, rn["latitude"], rn["longitude"])
            if d < min_dist:
                min_dist = d
                nearest = rn

        if nearest is None or min_dist > 800:
            continue

        # 生成名称
        if not name:
            building_type = tags.get("building", "building")
            amenity = tags.get("amenity", "")
            shop = tags.get("shop", "")
            if amenity:
                name = f"{amenity}_{node_idx}"
            elif shop:
                name = f"{shop}_{node_idx}"
            else:
                name = f"{building_type}_{node_idx}"

        # 避免重复名称
        existing_names = {n["name"] for n in road_nodes} | {n["name"] for n in poi_nodes}
        if name in existing_names:
            name = f"{name}_{node_idx}"

        poi_id = f"{node_prefix}_BLDG_{node_idx:06d}"
        node_idx += 1
        poi_node = {
            "id": poi_id,
            "map_id": map_id,
            "name": name,
            "type": ntype,
            "subtype": subtype,
            "latitude": center_lat,
            "longitude": center_lng,
        }
        poi_nodes.append(poi_node)

        # 创建双向连接边
        dist = max(min_dist, 0.1)
        edge_a = {
            "id": f"{edge_prefix}_BLDG_{node_idx:06d}",
            "map_id": map_id,
            "from": poi_id,
            "to": nearest["id"],
            "name": "",
            "distance": round(dist, 1),
            "congestion": 0.9,
            "ideal_speed_walk": ideal_speed_walk / 60.0,
            "ideal_speed_bike": 0,
            "ideal_speed_sightseeing_car": 0,
            "allowed_transport": list(transport_default),
            "road_type": "path",
            "geometry": [[center_lat, center_lng], [nearest["latitude"], nearest["longitude"]]],
        }
        poi_edges.append(edge_a)
        node_idx += 1

        edge_b = dict(edge_a)
        edge_b["id"] = f"{edge_prefix}_BLDG_{node_idx:06d}"
        edge_b["from"] = nearest["id"]
        edge_b["to"] = poi_id
        edge_b["geometry"] = [[nearest["latitude"], nearest["longitude"]], [center_lat, center_lng]]
        poi_edges.append(edge_b)
        node_idx += 1

    print(f"    Building POI nodes: {len(poi_nodes)}, connection edges: {len(poi_edges)}")
    return poi_nodes, poi_edges


def create_semantic_connections(pois, internal_nodes, map_id, config):
    """
    为语义 POI 创建节点和连接边。
    每个 POI: 找到最近道路节点 → 添加 POI 节点 + 连接边。
    """
    bbox = config["bbox"]
    transport_default = config["transport_default"]
    transport_extended = config["transport_extended"]
    node_prefix = config["node_prefix"]
    edge_prefix = config["edge_prefix"]
    ideal_speed_walk = config["ideal_speed_walk"]
    ideal_speed_bike = config.get("ideal_speed_bike")
    ideal_speed_sc = config.get("ideal_speed_sightseeing_car")

    random.seed(123)

    poi_nodes = []
    poi_edges = []
    edge_idx = 100000  # start from high number to avoid collision

    for poi in pois:
        # 找到最近道路节点
        nearest, min_dist = find_nearest_node(
            poi["lat"], poi["lng"], internal_nodes
        )

        if nearest is None:
            print(f"    WARNING: No road node near POI {poi['name']}")
            continue

        # 创建 POI 节点
        poi_node = {
            "id": poi["id"],
            "map_id": map_id,
            "name": poi["name"],
            "type": poi["type"],
            "subtype": None,
            "latitude": poi["lat"],
            "longitude": poi["lng"],
        }
        poi_nodes.append(poi_node)

        # 创建连接边（双向）
        dist = haversine_distance(poi["lat"], poi["lng"],
                                  nearest["latitude"], nearest["longitude"])
        if dist < 0.1:
            dist = 0.1  # 避免零距离边

        # POI → 最近道路节点
        poi_edges.append({
            "id": f"{edge_prefix}_{edge_idx:06d}",
            "map_id": map_id,
            "from": poi["id"],
            "to": nearest["id"],
            "distance": round(dist, 1),
            "congestion": 0.9,
            "ideal_speed_walk": ideal_speed_walk / 60.0,
            "ideal_speed_bike": (ideal_speed_bike / 60.0) if ideal_speed_bike else 0,
            "ideal_speed_sightseeing_car": (ideal_speed_sc / 60.0) if ideal_speed_sc else 0,
            "allowed_transport": list(transport_default),
            "road_type": "path",
            "geometry": [[poi["lat"], poi["lng"]],
                         [nearest["latitude"], nearest["longitude"]]],
        })
        edge_idx += 1

        # 最近道路节点 → POI
        poi_edges.append({
            "id": f"{edge_prefix}_{edge_idx:06d}",
            "map_id": map_id,
            "from": nearest["id"],
            "to": poi["id"],
            "distance": round(dist, 1),
            "congestion": 0.9,
            "ideal_speed_walk": ideal_speed_walk / 60.0,
            "ideal_speed_bike": (ideal_speed_bike / 60.0) if ideal_speed_bike else 0,
            "ideal_speed_sightseeing_car": (ideal_speed_sc / 60.0) if ideal_speed_sc else 0,
            "allowed_transport": list(transport_default),
            "road_type": "path",
            "geometry": [[nearest["latitude"], nearest["longitude"]],
                         [poi["lat"], poi["lng"]]],
        })
        edge_idx += 1

    print(f"    POI nodes: {len(poi_nodes)}, POI connection edges: {len(poi_edges)}")
    return poi_nodes, poi_edges


def create_facilities(config, all_nodes, map_id):
    """为真实地图生成设施点，连接到 POI 节点。"""
    facilities = []
    for fac_config in config["facilities"]:
        # 找到对应的 POI 节点
        linked_poi = None
        for n in all_nodes:
            if n["id"] == fac_config["poi_id"]:
                linked_poi = n
                break

        if linked_poi is None:
            print(f"    WARNING: POI {fac_config['poi_id']} not found for facility {fac_config['name']}")
            continue

        facilities.append({
            "id": fac_config["id"],
            "map_id": map_id,
            "name": fac_config["name"],
            "category": fac_config["category"],
            "linked_node_id": fac_config["poi_id"],
            "latitude": linked_poi["latitude"],
            "longitude": linked_poi["longitude"],
            "description": fac_config.get("description", ""),
        })

    print(f"    Facilities: {len(facilities)}")
    return facilities


def update_internal_maps(maps, map_id, source, tile_note):
    """更新 internal_maps.json 中指定地图的元数据。"""
    for m in maps:
        if m.get("map_id") == map_id:
            m["source"] = source
            m["is_real_map"] = True
            m["show_tile"] = True
            m["semi_real_map"] = False
            m["tile_note"] = tile_note
            # Update center
            return m
    return None


# ============================================================
# 主函数
# ============================================================

def import_map(map_id, config, existing_nodes, existing_edges, existing_facs, existing_maps):
    """导入单个地图的 OSM 数据。"""
    print(f"\n{'=' * 50}")
    print(f"导入地图: {map_id} - {config['name']}")
    print(f"{'=' * 50}")

    bbox = config["bbox"]
    highway_types = config["highway_types"]

    # 1. 查询 Overpass
    print(f"  查询 Overpass API...")
    print(f"    bbox: {bbox}")
    print(f"    highway types: {highway_types}")
    try:
        road_ways, building_ways, nodes_dict = query_overpass(bbox, highway_types)
        print(f"    Got {len(road_ways)} road ways, {len(building_ways)} building ways, {len(nodes_dict)} nodes from OSM")
    except Exception as e:
        print(f"  FAILED: Overpass query error: {e}")
        return False, str(e)

    # 2. 转换道路数据为 PathPal 图
    print(f"  转换道路数据...")
    new_nodes, new_edges, nc, ec, standalone_named, standalone_tagged = process_osm_data(
        road_ways, nodes_dict, map_id, config
    )

    if len(new_nodes) < 20:
        msg = f"OSM nodes too few: {len(new_nodes)} < 20 required"
        print(f"  FAILED: {msg}")
        return False, msg

    if len(new_edges) < 60:
        msg = f"OSM edges too few: {len(new_edges)} < 60 required"
        print(f"  FAILED: {msg}")
        return False, msg

    # 3. 添加语义 POI 节点
    print(f"  创建语义 POI 节点...")
    all_nodes = list(new_nodes)
    poi_nodes_sem, poi_edges_sem = create_semantic_connections(
        config["semantic_pois"], all_nodes, map_id, config
    )
    all_nodes.extend(poi_nodes_sem)

    # 4. 为 OSM 建筑轮廓创建 POI
    print(f"  处理 OSM 建筑数据...")
    poi_nodes_bldg, poi_edges_bldg = process_building_ways(
        building_ways, nodes_dict, all_nodes, map_id, config
    )
    all_nodes.extend(poi_nodes_bldg)

    # 5. 为 OSM 独立节点（命名+有标签）创建 POI
    print(f"  创建 OSM 节点 POI...")
    poi_nodes_osm, poi_edges_osm = create_named_node_pois(
        standalone_named, all_nodes, nodes_dict, map_id, config,
        standalone_tagged=standalone_tagged
    )
    all_nodes.extend(poi_nodes_osm)

    poi_nodes = poi_nodes_sem + poi_nodes_bldg + poi_nodes_osm
    poi_edges = poi_edges_sem + poi_edges_bldg + poi_edges_osm
    all_edges = new_edges + poi_edges

    # 4. 创建设施
    print(f"  创建设施...")
    facs = create_facilities(config, all_nodes, map_id)

    # 5. 打印统计
    lats = [n["latitude"] for n in all_nodes]
    lngs = [n["longitude"] for n in all_nodes]
    print(f"\n  统计:")
    print(f"    Total nodes: {len(all_nodes)} (OSM: {len(new_nodes)}, POI: {len(poi_nodes)})")
    print(f"    Total edges: {len(all_edges)} (OSM: {len(new_edges)}, POI: {len(poi_edges)})")
    print(f"    Facilities: {len(facs)}")
    print(f"    Lat range: [{min(lats):.6f}, {max(lats):.6f}]")
    print(f"    Lng range: [{min(lngs):.6f}, {max(lngs):.6f}]")
    print(f"    Edges with geometry: {sum(1 for e in all_edges if e.get('geometry'))}")

    # 6. 合并到现有数据（替换旧地图数据）
    print(f"  合并到现有数据...")
    # 移除旧数据
    old_node_ids = {n["id"] for n in existing_nodes if n.get("map_id") == map_id}
    old_edge_ids = {e["id"] for e in existing_edges if e.get("map_id") == map_id}
    old_fac_ids = {f["id"] for f in existing_facs if f.get("map_id") == map_id}

    existing_nodes[:] = [n for n in existing_nodes if n.get("map_id") != map_id]
    existing_edges[:] = [e for e in existing_edges if e.get("map_id") != map_id]
    existing_facs[:] = [f for f in existing_facs if f.get("map_id") != map_id]

    existing_nodes.extend(all_nodes)
    existing_edges.extend(all_edges)
    existing_facs.extend(facs)

    print(f"    移除了 {len(old_node_ids)} nodes, {len(old_edge_ids)} edges, {len(old_fac_ids)} facilities")
    print(f"    新增了 {len(all_nodes)} nodes, {len(all_edges)} edges, {len(facs)} facilities")

    # 7. 更新 internal_maps
    update_internal_maps(
        existing_maps, map_id,
        source="openstreetmap_vector",
        tile_note=f"该地图基于 OpenStreetMap 矢量道路数据构建，Dijkstra 在导入的 OSM 内部道路图上运行。{len(all_nodes)} 节点，{len(all_edges)} 边。"
    )
    # 更新 center
    for m in existing_maps:
        if m.get("map_id") == map_id:
            m["center"] = [
                round((min(lats) + max(lats)) / 2, 6),
                round((min(lngs) + max(lngs)) / 2, 6),
            ]

    return True, None


def fallback_manual_aligned(map_id, existing_nodes, existing_edges, existing_facs, existing_maps, config):
    """
    Fallback: 为人工数据添加 geometry（使用 from/to 节点坐标），更新 source 为 manual_osm_aligned。
    """
    print(f"\n  Fallback to manual_osm_aligned for {map_id}...")

    bbox = config["bbox"]
    map_nodes = [n for n in existing_nodes if n.get("map_id") == map_id]
    node_by_id = {n["id"]: n for n in map_nodes}
    map_edges = [e for e in existing_edges if e.get("map_id") == map_id]

    modified_count = 0
    for e in map_edges:
        if e.get("geometry"):
            continue
        fn = node_by_id.get(e["from"])
        tn = node_by_id.get(e["to"])
        if fn and tn:
            e["geometry"] = [
                [fn["latitude"], fn["longitude"]],
                [tn["latitude"], tn["longitude"]],
            ]
            modified_count += 1

    print(f"    Added geometry to {modified_count} edges")

    # 添加语义 POI 和连接边
    map_nodes_current = [n for n in existing_nodes if n.get("map_id") == map_id]
    poi_nodes, poi_edges = create_semantic_connections(
        config["semantic_pois"], map_nodes_current, map_id, config
    )
    existing_nodes.extend(poi_nodes)
    existing_edges.extend(poi_edges)

    # 替换设施
    existing_facs[:] = [f for f in existing_facs if f.get("map_id") != map_id]
    all_map_nodes = [n for n in existing_nodes if n.get("map_id") == map_id]
    facs = create_facilities(config, all_map_nodes, map_id)
    existing_facs.extend(facs)

    # 删除旧 POI 类型的重复节点（如果存在语义 POI 的旧节点 ID）
    # No action needed since old data was already filtered

    # 更新 internal_maps
    for m in existing_maps:
        if m.get("map_id") == map_id:
            m["source"] = "manual_osm_aligned"
            m["is_real_map"] = False
            m["show_tile"] = True
            m["semi_real_map"] = True
            m["tile_note"] = "该地图显示 OSM 真实瓦片，内部道路图为基于底图人工校准的半真实模型。路线沿道路节点连线绘制。"

    return True


def main():
    print("=" * 60)
    print("PathPal OSM Internal Map Import")
    print("=" * 60)

    # 加载现有数据
    with open(DATA_DIR / "internal_nodes.json", "r", encoding="utf-8") as f:
        existing_nodes = json.load(f)
    with open(DATA_DIR / "internal_edges.json", "r", encoding="utf-8") as f:
        existing_edges = json.load(f)
    with open(DATA_DIR / "facilities.json", "r", encoding="utf-8") as f:
        existing_facs = json.load(f)
    with open(DATA_DIR / "internal_maps.json", "r", encoding="utf-8") as f:
        existing_maps = json.load(f)

    original_counts = {
        "nodes": len(existing_nodes),
        "edges": len(existing_edges),
        "facilities": len(existing_facs),
    }

    results = {}
    fallback_needed = False

    for map_id in ["MAP_BUPT_REAL", "MAP_SCENIC_REAL"]:
        config = IMPORT_CONFIGS[map_id]
        success, error = import_map(
            map_id, config,
            existing_nodes, existing_edges, existing_facs, existing_maps
        )
        results[map_id] = {"success": success, "error": error}

        if not success:
            print(f"\n  OSM import FAILED for {map_id}: {error}")
            print(f"  Falling back to manual_osm_aligned...")
            fallback_needed = True
            fallback_manual_aligned(
                map_id, existing_nodes, existing_edges,
                existing_facs, existing_maps, config
            )
            results[map_id]["fallback"] = "manual_osm_aligned"

    # 写入数据文件
    print(f"\n{'=' * 50}")
    print("写入数据文件...")

    # Sort by ID for consistency
    existing_nodes.sort(key=lambda x: x["id"])
    existing_edges.sort(key=lambda x: x["id"])
    existing_facs.sort(key=lambda x: x["id"])

    with open(DATA_DIR / "internal_nodes.json", "w", encoding="utf-8") as f:
        json.dump(existing_nodes, f, ensure_ascii=False, indent=2)

    with open(DATA_DIR / "internal_edges.json", "w", encoding="utf-8") as f:
        json.dump(existing_edges, f, ensure_ascii=False, indent=2)

    with open(DATA_DIR / "facilities.json", "w", encoding="utf-8") as f:
        json.dump(existing_facs, f, ensure_ascii=False, indent=2)

    with open(DATA_DIR / "internal_maps.json", "w", encoding="utf-8") as f:
        json.dump(existing_maps, f, ensure_ascii=False, indent=2)

    # 汇总
    print(f"\n{'=' * 60}")
    print("导入汇总")
    print(f"{'=' * 60}")

    for map_id, result in results.items():
        status = "OSM vector import SUCCEEDED" if result["success"] else f"FAILED, fallback to {result.get('fallback', 'unknown')}"
        print(f"  {map_id}: {status}")
        if result["error"]:
            print(f"    Error: {result['error']}")

    print(f"\n  总节点: {original_counts['nodes']} → {len(existing_nodes)}")
    print(f"  总边: {original_counts['edges']} → {len(existing_edges)}")
    print(f"  总设施: {original_counts['facilities']} → {len(existing_facs)}")

    # 校验新数据
    print(f"\n{'=' * 50}")
    print("快速校验")
    for map_id in ["MAP_BUPT_REAL", "MAP_SCENIC_REAL"]:
        map_nodes = [n for n in existing_nodes if n.get("map_id") == map_id]
        map_edges = [e for e in existing_edges if e.get("map_id") == map_id]
        map_facs = [f for f in existing_facs if f.get("map_id") == map_id]
        geom_edges = [e for e in map_edges if e.get("geometry")]
        lats = [n["latitude"] for n in map_nodes]
        lngs = [n["longitude"] for n in map_nodes]
        print(f"\n  {map_id}:")
        print(f"    Nodes: {len(map_nodes)}, Edges: {len(map_edges)}, Facilities: {len(map_facs)}")
        print(f"    Edges with geometry: {len(geom_edges)}/{len(map_edges)}")
        if lats:
            print(f"    Bbox: lat [{min(lats):.6f}, {max(lats):.6f}], lng [{min(lngs):.6f}, {max(lngs):.6f}]")

        source = ""
        for m in existing_maps:
            if m.get("map_id") == map_id:
                source = m.get("source", "?")
                break
        print(f"    Source: {source}")

    if fallback_needed:
        print(f"\n  RESULT: OSM vector import FAILED for some maps, fallback to manual_osm_aligned.")
        return 1
    else:
        print(f"\n  RESULT: OSM vector import SUCCEEDED for all maps.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
