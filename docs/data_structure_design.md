# 数据结构设计文档 (Data Structure Design)

## 1. destinations.json — 目的地数据

存储至少 200 个景区和校园。

```json
[
  {
    "id": "DEST_001",
    "name": "北京邮电大学",
    "type": "campus",
    "category": "university",
    "keywords": ["通信", "计算机", "信息"],
    "popularity": 95,
    "rating": 4.7,
    "latitude": 39.9620,
    "longitude": 116.3500,
    "description": "北京邮电大学是教育部直属...",
    "tags": ["211", "双一流", "工科"],
    "internal_map_id": "MAP_CAMPUS_001"
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 主键，格式 DEST_XXX |
| name | string | 目的地名称 |
| type | string | campus / attraction |
| category | string | university, park, museum, palace, temple, stadium, zoo, historical_site 等 |
| keywords | string[] | 搜索关键词 |
| popularity | number | 热度值 (0-100) |
| rating | number | 评分 (0-5.0) |
| latitude | number | 纬度 |
| longitude | number | 经度 |
| description | string | 简介 |
| tags | string[] | 标签 |
| internal_map_id | string | 绑定的内部地图 ID |

## 2. internal_maps.json — 内部地图元数据

定义少量地图模板，供 200 个 destination 复用。

```json
[
  {
    "id": "MAP_CAMPUS_001",
    "name": "校园标准模板",
    "type": "campus",
    "description": "适用于大学校园的内部地图模板",
    "default_center_lat": 39.9620,
    "default_center_lng": 116.3500,
    "default_zoom": 16
  },
  {
    "id": "MAP_SCENIC_001",
    "name": "景区标准模板",
    "type": "attraction",
    "description": "适用于景区/公园的内部地图模板",
    "default_center_lat": 39.9163,
    "default_center_lng": 116.3972,
    "default_zoom": 16
  },
  {
    "id": "MAP_MIXED_001",
    "name": "综合园区模板",
    "type": "mixed",
    "description": "适用于大型综合园区的内部地图模板",
    "default_center_lat": 39.9929,
    "default_center_lng": 116.3255,
    "default_zoom": 16
  }
]
```

## 3. internal_nodes.json — 内部节点

每个地图的节点集合，包括建筑物、景点、路口、大门等。

```json
[
  {
    "id": "NODE_C001_G01",
    "map_id": "MAP_CAMPUS_001",
    "name": "西门",
    "type": "gate",
    "subtype": null,
    "latitude": 39.9615,
    "longitude": 116.3490
  },
  {
    "id": "NODE_C001_T01",
    "map_id": "MAP_CAMPUS_001",
    "name": "第三教学楼",
    "type": "teaching_building",
    "subtype": null,
    "latitude": 39.9625,
    "longitude": 116.3510
  },
  {
    "id": "NODE_C001_I01",
    "map_id": "MAP_CAMPUS_001",
    "name": "主路-西门路口",
    "type": "intersection",
    "subtype": "crossroad",
    "latitude": 39.9620,
    "longitude": 116.3495
  },
  {
    "id": "NODE_C001_L01",
    "map_id": "MAP_CAMPUS_001",
    "name": "图书馆",
    "type": "library",
    "subtype": null,
    "latitude": 39.9630,
    "longitude": 116.3505
  },
  {
    "id": "NODE_C001_D01",
    "map_id": "MAP_CAMPUS_001",
    "name": "学生宿舍1号楼",
    "type": "dormitory",
    "subtype": null,
    "latitude": 39.9640,
    "longitude": 116.3515
  },
  {
    "id": "NODE_C001_CA01",
    "map_id": "MAP_CAMPUS_001",
    "name": "第一食堂",
    "type": "canteen",
    "subtype": null,
    "latitude": 39.9635,
    "longitude": 116.3508
  },
  {
    "id": "NODE_C001_F01",
    "map_id": "MAP_CAMPUS_001",
    "name": "校园超市挂接点",
    "type": "facility_point",
    "subtype": "supermarket",
    "latitude": 39.9632,
    "longitude": 116.3512
  }
]
```

### 节点类型枚举

| type | 说明 |
|------|------|
| gate | 大门/出入口 |
| intersection | 道路交叉口 |
| scenic_spot | 景点 |
| teaching_building | 教学楼 |
| office_building | 办公楼 |
| dormitory | 宿舍楼 |
| library | 图书馆 |
| canteen | 食堂 |
| facility_point | 服务设施挂接点 |
| classroom_building | 综合教室楼 |

## 4. internal_edges.json — 内部道路边

边数 >= 200。

```json
[
  {
    "id": "EDGE_C001_001",
    "map_id": "MAP_CAMPUS_001",
    "from": "NODE_C001_G01",
    "to": "NODE_C001_I01",
    "distance": 120,
    "congestion": 0.9,
    "ideal_speed_walk": 1.2,
    "ideal_speed_bike": 4.0,
    "ideal_speed_sightseeing_car": 0,
    "allowed_transport": ["walk", "bike"],
    "road_type": "main_road"
  },
  {
    "id": "EDGE_C001_002",
    "map_id": "MAP_CAMPUS_001",
    "from": "NODE_C001_I01",
    "to": "NODE_C001_T01",
    "distance": 200,
    "congestion": 0.8,
    "ideal_speed_walk": 1.2,
    "ideal_speed_bike": 4.0,
    "ideal_speed_sightseeing_car": 0,
    "allowed_transport": ["walk", "bike"],
    "road_type": "main_road"
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 主键 |
| map_id | string | 所属地图 ID |
| from | string | 起点节点 ID |
| to | string | 终点节点 ID |
| distance | number | 距离（米） |
| congestion | number | 拥挤系数 (0 < c <= 1) |
| ideal_speed_walk | number | 理想步行速度 (m/s) |
| ideal_speed_bike | number | 理想自行车速度 (m/s) |
| ideal_speed_sightseeing_car | number | 理想电瓶车速度 (m/s)，0 表示不支持 |
| allowed_transport | string[] | 允许的交通工具 |
| road_type | string | 道路类型：main_road, path, trail, sightseeing_route 等 |

### 速度/时间公式

```
real_speed = congestion × ideal_speed
time = distance / real_speed（秒）
```

无向图：每条边双向可通行。Dijkstra 时对 `from → to` 和 `to → from` 均做松弛。

## 5. facilities.json — 服务设施

数量 >= 50，类别 >= 10。

```json
[
  {
    "id": "FAC_C001_001",
    "map_id": "MAP_CAMPUS_001",
    "name": "校园超市",
    "category": "supermarket",
    "linked_node_id": "NODE_C001_F01",
    "latitude": 39.9632,
    "longitude": 116.3512,
    "description": "位于食堂一层的综合性超市"
  }
]
```

### 设施类别

| category | 说明 |
|----------|------|
| toilet | 洗手间 |
| shop | 商店 |
| restaurant | 饭店 |
| library | 图书馆 |
| canteen | 食堂 |
| supermarket | 超市 |
| cafe | 咖啡馆 |
| office | 办公室 |
| dormitory | 宿舍楼 |
| classroom | 教室 |
| 可扩展 | ... |

## 6. users.json — 用户数据

数量 >= 10。

```json
[
  {
    "id": "USER_001",
    "username": "旅行者小王",
    "interests": ["历史", "建筑", "自然风光"],
    "favorite_categories": ["museum", "park", "palace"],
    "preferred_tags": ["世界遗产", "5A景区", "免费"]
  }
]
```

## 7. indoor_graphs.json（可选 Demo）

用于简单室内导航 Demo。结构同 internal_nodes/edges，但 scale 更小。
例如一个教学楼内部或图书馆内部的楼层导航。

当前包含 1 个 building：BUILDING_BUPT_MAIN（北邮主楼），含 2 层楼、8 个节点、14 条边。

```json
{
  "indoor_maps": [
    {
      "building_id": "BUILDING_BUPT_MAIN",
      "name": "北京邮电大学主楼",
      "floors": 2,
      "nodes": [...],
      "edges": [...]
    }
  ]
}
```

## 数据关系图

```
destinations.json
  └── internal_map_id ──────┐
                             │
internal_maps.json           │
  └── id ←──────────────────┘
        │
        ├── internal_nodes.json  (map_id)
        ├── internal_edges.json  (map_id)
        │     ├── from → internal_nodes.id
        │     └── to   → internal_nodes.id
        └── facilities.json      (map_id)
              └── linked_node_id → internal_nodes.id
```

## 8. 核心设计决策

### 为什么 200 个目的地可以复用内部地图？

当前设计使用 **3 个内部地图模板**（校园模板、景区模板、综合园区模板），217 个目的地通过 `internal_map_id` 字段绑定其中一个模板。这样：

- 30 个 campus 类型目的地全部绑定 MAP_CAMPUS_001
- 约 100 个 attraction 绑定 MAP_SCENIC_001
- 约 87 个 attraction 绑定 MAP_MIXED_001

路线规划和场所查询时，后端根据 `destination_id` → `internal_map_id` 加载对应地图的 nodes + edges，**在同一套图内**运行 Dijkstra。

### 引用完整性约束

生成脚本和校验脚本共同保证：
1. `destinations.internal_map_id` → `internal_maps.id` 存在
2. `internal_edges.from / to` → `internal_nodes.id` 存在且 map_id 一致
3. `facilities.linked_node_id` → `internal_nodes.id` 存在且 map_id 一致
4. campus 图中的边不含 sightseeing_car
5. scenic 图中的边不含 bike

### 当前数据规模验证

所有数据约束已通过 `validate_data.py` 校验（4228 checks passed）。详见 [data_validation_report.md](data_validation_report.md)。
