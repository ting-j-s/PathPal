# API 设计文档 (API Design)

## 基础约定

- Base URL: `http://127.0.0.1:5000/api`
- Content-Type: `application/json`
- 错误格式: `{"error": "描述", "type": "ValueError|FileNotFoundError|InternalError"}`
- 健康检查: `GET /api/health`
- 统计信息: `GET /api/stats`

---

## 系统 API

### GET /api/health

返回：
```json
{
  "status": "ok",
  "project": "PathPal",
  "phase": "phase1-backend-api"
}
```

### GET /api/stats

返回：
```json
{
  "destinations": 217,
  "internal_maps": 3,
  "internal_nodes": 112,
  "internal_edges": 284,
  "facilities": 52,
  "facility_categories": 12,
  "users": 12,
  "indoor_buildings": 1
}
```

---

## 模块一：旅游推荐 API

Blueprint: `recommendation_bp`, prefix: `/api`

### 1.1 目的地列表

```
GET /api/destinations?limit=10&type=campus
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量上限 |
| type | string | 否 | campus / attraction |

### 1.2 目的地详情

```
GET /api/destinations/<destination_id>
```

返回单个目的地详情。不存在时返回 400。

### 1.3 热点推荐 Top-K

```
GET /api/recommendations/hot?k=10
```

按 popularity 降序取 Top-K（Top-K Heap 算法）。

### 1.4 评分推荐 Top-K

```
GET /api/recommendations/rating?k=10
```

按 rating 降序取 Top-K（Top-K Heap 算法）。

### 1.5 个性化推荐

```
GET /api/recommendations/interest?user_id=USER_001&k=10
```

根据用户 interests / favorite_categories / preferred_tags 计算匹配分：
- `interest_score = match_count * 10 + popularity * 0.2 + rating * 10`
- 返回 `interest_score`, `recommendation_reason`, `matched_terms`

### 1.6 关键词搜索

```
GET /api/destinations/search?keyword=故宫&sort_by=popularity
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| sort_by | string | 否 | popularity / rating |

### 1.7 按类别过滤

```
GET /api/destinations/category?category=park&sort_by=popularity
```

---

## 模块二：路线规划 API

Blueprint: `route_bp`, prefix: `/api`

所有路线 API 必须包含 `destination_id`，路线规划仅在 `internal_map_id` 内部进行。

### 2.1 获取内部地图节点

```
GET /api/route/nodes?destination_id=DEST_001
```

### 2.2 最短距离路线

```
GET /api/route/shortest-distance?destination_id=DEST_001&start=NODE_CAM_001&end=NODE_CAM_004
```

边权 = distance，Dijkstra。

### 2.3 最短时间路线

```
GET /api/route/shortest-time?destination_id=DEST_001&start=NODE_CAM_001&end=NODE_CAM_004&transport=walk
```

| transport | 校园 | 景区 |
|-----------|------|------|
| walk | 支持 | 支持 |
| bike | 支持 | 禁止（400） |
| sightseeing_car | 禁止（400） | 支持 |

### 2.4 混合交通时间

```
GET /api/route/mixed-time?destination_id=DEST_001&start=NODE_CAM_001&end=NODE_CAM_004
```

每条边自动选择最快交通工具。校园：walk/bike；景区：walk/sightseeing_car；mixed：三者均可。

### 2.6 多点路线（贪心 TSP）

```
POST /api/route/multi-point
Content-Type: application/json

{
  "destination_id": "DEST_001",
  "start": "NODE_CAM_001",
  "targets": ["NODE_CAM_005", "NODE_CAM_008"],
  "strategy": "shortest_distance"
}
```

strategy: shortest_distance / shortest_time / mixed_time

### 路线规划通用响应格式

```json
{
  "destination_id": "DEST_001",
  "destination_name": "北京邮电大学",
  "destination_type": "campus",
  "internal_map_id": "MAP_CAMPUS_001",
  "strategy": "mixed_time",
  "algorithm": "Dijkstra",
  "formula": "每边自动选择最快交通工具",
  "reachable": true,
  "path": ["NODE_CAM_001", "NODE_CAM_002", "NODE_CAM_005"],
  "coordinates": [[39.960, 116.347], [39.960, 116.349], ...],
  "total_distance": 412.0,
  "total_time": 245.3,
  "segments": [
    {
      "from": "NODE_CAM_001",
      "to": "NODE_CAM_002",
      "from_name": "路口-(0,0)",
      "to_name": "路口-(0,1)",
      "distance": 207.0,
      "transport": "bike",
      "congestion": 0.9,
      "ideal_speed": 4.0,
      "real_speed": 3.6,
      "time": 57.5
    }
  ],
  "note": "路线规划仅在景区/校园内部道路图中进行，不是城市级外部导航"
}
```

---

## 模块三：场所查询 API

Blueprint: `nearby_bp`, prefix: `/api`

所有 nearby 查询必须包含 `destination_id` 和 `node_id`。排序依据为道路网络最短路径距离。

### 3.1 附近设施查询

```
GET /api/nearby?destination_id=DEST_001&node_id=NODE_CAM_001&radius=1000
```

### 3.2 按类别过滤

```
GET /api/nearby/category?destination_id=DEST_001&node_id=NODE_CAM_001&category=toilet&radius=500
```

### 3.3 关键词搜索

```
GET /api/nearby/search?destination_id=DEST_001&node_id=NODE_CAM_001&keyword=超市&radius=1000
```

### 3.4 设施类别列表

```
GET /api/nearby/categories?destination_id=DEST_001
```

### 3.5 设施列表

```
GET /api/nearby/facilities?destination_id=DEST_001
```

### 响应格式

```json
{
  "destination_id": "DEST_001",
  "destination_name": "北京邮电大学",
  "internal_map_id": "MAP_CAMPUS_001",
  "origin": "NODE_CAM_001",
  "algorithm": "Dijkstra + Road Distance Sorting (Merge Sort)",
  "data_structure": "Internal Graph Adjacency List",
  "note": "排序依据为道路网络最短路径距离，不是经纬度直线距离",
  "count": 5,
  "facilities": [
    {
      "id": "FAC_C001_001",
      "name": "校园超市",
      "category": "supermarket",
      "linked_node_id": "NODE_CAM_014",
      "road_distance": 234.5,
      "path": ["NODE_CAM_001", "NODE_CAM_002", "NODE_CAM_014"],
      "coordinates": [39.963, 116.351]
    }
  ]
}
```

---

## 模块四：室内导航 API（Demo）

Blueprint: `indoor_bp`, prefix: `/api`

### 4.1 建筑列表

```
GET /api/indoor/buildings
```

### 4.2 室内路线

```
GET /api/indoor/route?building_id=BUILDING_BUPT_MAIN&start=IN_B101&end=IN_B201
```

---

## 错误码约定

| HTTP | type | 触发条件 |
|------|------|----------|
| 200 | — | 正常 |
| 400 | ValueError | 参数缺失、资源不存在、业务校验失败 |
| 500 | FileNotFoundError | 数据文件缺失 |
| 500 | InternalError | 其他服务器异常 |

---

## 算法/数据结构声明

所有 API 响应均返回算法和数据结构信息：

| 接口 | algorithm | data_structure |
|------|-----------|----------------|
| 热门推荐 | Top-K Heap | Array + Min-Heap (size K) |
| 评分推荐 | Top-K Heap | Array + Min-Heap (size K) |
| 兴趣推荐 | Top-K Heap (Interest Score) | Array + Min-Heap (size K) |
| 搜索 | Linear Search + Quick Sort | Array |
| 类别过滤 | Exact Filter + Quick Sort | Array |
| 路线规划 | Dijkstra | Internal Graph Adjacency List |
| 附近设施 | Dijkstra + Road Distance Sorting (Merge Sort) | Internal Graph Adjacency List |
| 室内导航 | Dijkstra (Indoor Graph) | Indoor Graph Adjacency List |
