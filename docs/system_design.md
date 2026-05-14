# 系统设计文档 (System Design)

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 (Frontend)                           │
│  HTML + CSS + JS + Leaflet                                  │
│  ├─ index.html            主页                              │
│  ├─ recommendation.html   旅游推荐                          │
│  ├─ route_planning.html   路线规划                          │
│  ├─ nearby.html           场所查询                          │
│  ├─ indoor_navigation.html 室内导航 Demo                    │
│  ├─ css/style.css         统一样式                          │
│  └─ js/                                                    │
│      ├─ api.js              API 调用封装 (PathPalAPI)       │
│      ├─ map.js              Leaflet 地图交互 (PathPalMap)   │
│      ├─ index.js            首页统计加载                    │
│      ├─ recommendation.js   推荐交互                        │
│      ├─ route_planning.js   路线规划交互 + 地图渲染          │
│      ├─ nearby.js           场所查询交互 + 地图渲染          │
│      └─ indoor_navigation.js 室内导航交互                   │
├─────────────────────────────────────────────────────────────┤
│                 后端 (Flask Backend)                         │
│  ├─ routes/            API 路由层（4 个蓝图）               │
│  ├─ services/          业务逻辑层（5 个服务）               │
│  │   ├─ data_loader.py     统一数据加载（内存缓存）         │
│  │   ├─ recommendation_service.py  推荐服务                 │
│  │   ├─ route_service.py          路线规划服务              │
│  │   ├─ nearby_service.py         场所查询服务              │
│  │   └─ indoor_service.py         室内导航服务              │
│  ├─ algorithms/      核心算法层（自实现，6 个模块）         │
│  └─ scripts/          数据工具脚本                           │
│      ├─ generate_seed_data.py  数据生成                      │
│      └─ validate_data.py       数据校验                      │
├─────────────────────────────────────────────────────────────┤
│                 数据层 (JSON Files)                          │
│  ├─ destinations.json    217 目的地                         │
│  ├─ internal_maps.json   8 个地图模板                       │
│  ├─ internal_nodes.json  21,006 个内部节点                  │
│  ├─ internal_edges.json  46,114 条道路边                    │
│  ├─ facilities.json      1,740 个服务设施（28 类别）        │
│  ├─ users.json           12 个用户                          │
│  └─ indoor_graphs.json   1 个室内建筑 Demo                  │
└─────────────────────────────────────────────────────────────┘
```

## 分层职责

### 路由层 (routes/) — 4 个蓝图

| 蓝图 | 文件 | 端点数 | 前缀 |
|------|------|--------|------|
| recommendation_bp | recommendation_routes.py | 7 | /api |
| route_bp | route_routes.py | 6 | /api |
| nearby_bp | nearby_routes.py | 5 | /api |
| indoor_bp | indoor_routes.py | 2 | /api |

职责：
- 解析 HTTP 请求参数
- 校验必填参数，缺失时返回 400
- 调用 service 层处理业务
- 返回 JSON 响应
- ValueError → 400, FileNotFoundError → 500

### 服务层 (services/) — 5 个服务

| 服务 | 职责 |
|------|------|
| data_loader | 统一读取 data/ 下 JSON 文件，提供内存缓存和 ID 查询 |
| RecommendationService | 热点/评分/兴趣推荐、关键词搜索、类别过滤 |
| RouteService | 4 种路线策略 + 多点 TSP 贪心 + 交通校验 |
| NearbyService | 道路距离附近查询、类别/关键词过滤 |
| IndoorService | 室内导航 Demo（建筑列表、室内路径） |

服务层调用 algorithm 层的自定义算法（Top-K、排序、查找、Dijkstra），不依赖任何第三方算法库。

### 算法层 (algorithms/) — 6 个模块

| 模块 | 算法 |
|------|------|
| graph.py | 邻接表图、从 JSON 加载 |
| sorting.py | 快速排序、归并排序、堆排序、多键排序 |
| search.py | 线性查找、哈希索引、关键词匹配、字段过滤 |
| topk.py | 小顶堆 Top-K、快速选择 Top-K |
| dijkstra.py | Dijkstra（4 种权函数）+ 单源全节点 + 路径重建 + 多点贪心 TSP |
| nearby.py | 道路距离附近设施查询 |

所有算法自行实现，不依赖 networkx、osmnx、heapq 等库。

### 模型层 (models/)

当前仅包含 `__init__.py`。数据模型通过 dict 直接操作，JSON schema 定义见 [data_structure_design.md](data_structure_design.md)。

## 数据流

### 推荐流程

```
用户请求 → recommendation_routes.py
  → RecommendationService
    → data_loader 加载 destinations.json + users.json
    → algorithms.topk (Top-K Heap) / algorithms.sorting (Quick Sort)
    → algorithms.search (Linear Search / Hash Index)
  → 返回 JSON 推荐列表
```

### 路线规划流程

```
用户请求 → route_routes.py
  → RouteService
    → data_loader 通过 destination_id 获取 internal_map_id
    → data_loader.load_graph_for_destination() 构建邻接表图
    → algorithms.dijkstra 计算最短路径
    → 交通校验（campus 拒绝 sightseeing_car，attraction 拒绝 bike）
    → 返回 path、segments、total_distance、total_time、note
```

路线规划仅在同一 internal_map_id 内部进行，不做跨地图路线。

### 场所查询流程

```
用户请求 → nearby_routes.py
  → NearbyService
    → data_loader 通过 destination_id 获取 graph + facilities
    → algorithms.dijkstra_all_distances 一次单源 Dijkstra，得到所有节点最短距离
    → algorithms.nearby 查表 O(1) 获取每个设施道路距离 + 按需回溯路径
    → 类别/关键词/半径过滤
    → algorithms.sorting.merge_sort 按 road_distance 升序
    → 返回 facilities + road_distance + path + route_geometry + note
```

排序依据为道路网络最短路径距离，不使用经纬度直线距离。单个设施查询 O(1) 查表，整体复杂度 O(V² + F log F)。

### 室内导航流程（Demo）

```
用户请求 → indoor_routes.py
  → IndoorService
    → data_loader 加载 indoor_graphs.json
    → 构建室内图 → algorithms.dijkstra
    → 返回 steps
```

## 关键设计决策

1. **内部地图复用**：217 个目的地通过 `internal_map_id` 复用 3 套内部地图模板（校园/景区/综合），避免为每个目的地单独制作地图
2. **按需构建图**：每次请求从 JSON 全量加载 nodes + edges，按 `map_id` 筛选构建邻接表（抽象模板 ≤ 40 节点，OSM 真实地图 ≤ 12,008 节点；均使用 O(V²) Dijkstra，构建时间可忽略）
3. **内存缓存**：data_loader 对每个 JSON 文件只读一次，后续请求命中缓存
4. **无状态服务**：不持久化 session，user_id 通过请求参数传递
5. **自定义算法**：所有排序、搜索、最短路、Top-K 算法均自行实现，不依赖第三方库
6. **无数据库**：所有数据存储在 JSON 文件中

## 前端架构

### 页面结构

| 页面 | 文件 | JS 模块 | Leaflet |
|------|------|---------|---------|
| 首页 | index.html | index.js | — |
| 旅游推荐 | recommendation.html | recommendation.js | — |
| 内部路线规划 | route_planning.html | route_planning.js | 是 |
| 场所查询 | nearby.html | nearby.js | 是 |
| 室内导航 Demo | indoor_navigation.html | indoor_navigation.js | — |

### JS 模块职责

| 模块 | 挂载点 | 职责 |
|------|--------|------|
| api.js | window.PathPalAPI | API 调用封装、错误/加载提示、距离/时间格式化 |
| map.js | window.PathPalMap | Leaflet 地图创建、图层管理、路线/标记绘制 |

### API 调用关系

```
index.js       → GET /api/stats

recommendation.js → GET /api/recommendations/hot
                    GET /api/recommendations/rating
                    GET /api/recommendations/interest
                    GET /api/destinations/search
                    GET /api/destinations/category
                    GET /api/destinations

route_planning.js → GET /api/destinations
                    GET /api/route/nodes
                    GET /api/route/shortest-distance
                    GET /api/route/shortest-time
                    GET /api/route/mixed-time
                    POST /api/route/multi-point

nearby.js         → GET /api/destinations
                    GET /api/route/nodes
                    GET /api/nearby
                    GET /api/nearby/category
                    GET /api/nearby/search
                    GET /api/nearby/categories

indoor_navigation.js → GET /api/indoor/buildings
                       GET /api/indoor/route
```

### Leaflet 地图展示方式

路线规划和场所查询页面使用 Leaflet 显示内部道路图：
- **路线规划**：起点/终点标记 + polyline 路线 + 分段交通方式颜色区分
  - walk → 蓝色, bike → 绿色, sightseeing_car → 橙色
- **场所查询**：当前节点标记 + 设施标记（带 popup 显示名称/类别/道路距离）
  - 点击"查看路径"后绘制起点到设施的 Dijkstra 最短路径
- 地图使用 OpenStreetMap 瓦片，自动 fitBounds 适应路线范围
- 不使用任何城市级导航服务
