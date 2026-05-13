# 算法设计文档 (Algorithm Design)

## 概述

所有核心算法自行实现，不依赖第三方库。算法模块位于 `backend/algorithms/`。

---

## 1. 图数据结构（邻接表）

**文件**：[backend/algorithms/graph.py](../backend/algorithms/graph.py)

### 1.1 Graph 类

```
类：Graph
构造参数：
  - map_id: str, 地图 ID
  - directed: bool, 是否有向图（默认 False）

内部结构：
  - self.nodes: dict[node_id → node_data]
  - self.adjacency: dict[node_id → [edge_data, ...]]
  - self.edges: [edge_data, ...]
```

**实现说明**：
- 核心使用 Python 内置 `dict` + `list` 构建邻接表，不使用任何第三方图库。
- 无向图：调用 `add_edge` 时自动将边同时加入 `adjacency[from]` 和 `adjacency[to]`。
- 有向图：仅加入 `adjacency[from]`。

### 1.2 方法列表

| 方法 | 说明 |
|------|------|
| `add_node(node_id, node_data)` | 添加节点 |
| `add_edge(edge_data)` | 添加边（无向图双向加入邻接表） |
| `get_node(node_id)` | 获取节点数据 |
| `get_neighbors(node_id)` | 获取该节点的所有邻接边列表 |
| `get_edge(from_id, to_id)` | 查找两点之间的边 |
| `has_node(node_id)` | 判断节点是否存在 |
| `node_count()` | 返回节点总数 |
| `edge_count()` | 返回边总数 |
| `get_coordinates(node_id)` | 返回 `[latitude, longitude]` 或 `None` |
| `get_node_name(node_id)` | 返回节点名称，无名称则返回 node_id |

### 1.3 图加载函数

```
load_graph_from_data(nodes, edges, map_id, directed=False)
  - nodes: list of node dicts
  - edges: list of edge dicts
  - 筛选 node["map_id"] == map_id 的节点
  - 筛选 edge["map_id"] == map_id 的边
  - 校验 edge.from / edge.to 均存在于已加载节点中
  - 无向图自动去重（按 sorted([from, to]) 去重）
  - 返回 Graph 对象

load_graph_from_files(nodes_file, edges_file, map_id, directed=False)
  - 读取 JSON 文件，调用 load_graph_from_data
```

---

## 2. 排序算法

**文件**：[backend/algorithms/sorting.py](../backend/algorithms/sorting.py)

三种排序算法均有独立实现，不依赖 Python 内置 `sorted()` 或 `list.sort()`。

### 2.1 quick_sort(items, key=None, reverse=False)

- 经典快速排序，Lomuto 分区方案，取最右元素为 pivot
- 返回新列表，不修改原列表
- 支持 key 为 `callable`、`str`（字段名）或 `None`

### 2.2 merge_sort(items, key=None, reverse=False)

- 自顶向下归并排序，稳定排序
- 用于 `multi_key_sort` 中逐级稳定排序

### 2.3 heap_sort(items, key=None, reverse=False)

- 自行实现堆化（`_heapify`），不使用 `heapq` 库
- 建堆 + 逐个提取，与标准堆排序一致

### 2.4 multi_key_sort(items, key_specs)

- 多键排序：从低优先级 key 开始到高优先级，依次用 stable 的 merge_sort
- `key_specs` 格式：`[("field_name", reverse_bool), ...]`
- 支持 item 为 dict

### 2.5 get_value(item, key)

- 工具函数：支持 callable、str（字段名）、None 三种 key 形式

---

## 3. 查找 / 搜索算法

**文件**：[backend/algorithms/search.py](../backend/algorithms/search.py)

### 3.1 linear_search(items, keyword, fields)

- 线性扫描，O(N)
- 字符串字段：大小写不敏感子串匹配
- 列表字段：逐个元素匹配
- 数值字段：转为字符串匹配
- 适用于中文关键词搜索

### 3.2 exact_search(items, value, field)

- 精确等值匹配

### 3.3 build_hash_index(items, field) + hash_search(index, value)

- 构建 `{field_value_str: [item, ...]}` 哈希索引
- O(1) 查找

### 3.4 keyword_search / filter_by_field / filter_by_map_id

- 业务语义封装接口

---

## 4. Top-K 算法

**文件**：[backend/algorithms/topk.py](../backend/algorithms/topk.py)

### 4.1 top_k_heap(items, k, key=None, reverse=True)

- 维护大小为 k 的堆（自行实现 `_sift_up` / `_sift_down`，不依赖 `heapq`）
- `reverse=True`：取 key 最大的前 k 个 → 维护**小顶堆**（堆顶最小，新值 > 堆顶则进入）
- `reverse=False`：取 key 最小的前 k 个 → 维护**大顶堆**（堆顶最大，新值 < 堆顶则进入）
- 返回的 k 个元素内部用 `quick_sort` 排好序
- 时间复杂度：O(N log K)，空间复杂度：O(K)
- **不使用完整排序后切片**

### 4.2 top_k_quickselect(items, k, key=None, reverse=True)

- 快速选择（Quickselect）：分区到第 k 个位置即停止
- 期望 O(N)，最坏 O(N²)
- 返回的 k 个元素内部用 `quick_sort` 排好序

### 4.3 get_top_k_by_field(items, k, field, reverse=True)

- 针对 dict 的字段取 Top-K，内部调用 `top_k_heap`

---

## 5. Dijkstra 最短路径

**文件**：[backend/algorithms/dijkstra.py](../backend/algorithms/dijkstra.py)

### 5.1 通用 Dijkstra 框架

```
dijkstra(graph, start, end, weight_func) → dict

weight_func(edge) → {
    "weight": float,      # 边权
    "transport": str,     # 交通工具
    "time": float,        # 通行时间
    "ideal_speed": float,
    "real_speed": float,
}
```

**实现要点**：
- 使用数组 + 线性扫描未访问节点（O(V²)），适用于 V ~ 40 的小规模图
- 不依赖 `heapq` 做优先队列（更简单且对小图足够快）
- 无向图：松弛 `from→to` 和 `to→from` 两个方向
- 返回完整 path、segments、total_distance、total_time

**返回结构**：
```
{
    "path": [node_id, ...],
    "total_distance": float,
    "total_time": float,
    "segments": [
        {
            "from": ..., "to": ...,
            "from_name": ..., "to_name": ...,
            "distance": float,
            "transport": str,
            "congestion": float,
            "ideal_speed": float,
            "real_speed": float,
            "time": float
        }, ...
    ],
    "reachable": bool
}
```

### 5.2 calculate_edge_time(edge, transport)

- 根据 transport 查 ideal_speed → `real_speed = congestion × ideal_speed` → `time = distance / real_speed`
- transport 不在 `allowed_transport` 中或 ideal_speed ≤ 0 → 返回 `None`（边不可通行）

### 5.3 choose_best_transport_for_edge(edge, destination_type)

- `campus`：候选 {walk, bike}
- `attraction`：候选 {walk, sightseeing_car}
- `mixed`：候选 {walk, bike, sightseeing_car}
- 返回该边最快交通工具的时间信息

### 5.4 四种路线策略

| 函数 | 边权 | 说明 |
|------|------|------|
| `dijkstra_shortest_distance(graph, start, end)` | `distance` | 最短距离，time 用 walk 估算 |
| `dijkstra_shortest_time(graph, start, end, transport)` | `time` | 指定交通工具最短时间 |
| `dijkstra_mixed_time(graph, start, end, destination_type)` | 每边自动选最快 | 混合交通时间最短 |

### 5.5 multi_point_route(graph, start, targets, strategy, destination_type)

- **贪心 TSP 近似**：从 start 出发，每次选距离/时间最近的未访问目标，最后返回 start
- 支持 `shortest_distance`、`shortest_time`、`mixed_time` 三种策略
- 返回完整合并后的 path、segments、visit_order
- 文档明确说明这是贪心近似，非最优解

### 5.6 错误处理

- start/end 不存在：`raise ValueError`
- 不可达：返回 `reachable: False`, `total_distance: INF`, `total_time: INF`, `path: []`

---

## 6. 附近设施道路距离查询

**文件**：[backend/algorithms/nearby.py](../backend/algorithms/nearby.py)

### 6.1 calculate_nearby_facilities_by_road_distance(graph, origin_node_id, facilities, radius, category, keyword)

**流程**：
1. 类别过滤（category 参数）
2. 关键词过滤（keyword 匹配 name/category/description）
3. 对每个候选 facility，用 `dijkstra_shortest_distance` 计算 origin → linked_node_id 的道路最短距离
4. 半径过滤（radius 参数）
5. 按 `road_distance` 升序排序（使用 `merge_sort`）

**关键约束**：
- 禁止使用经纬度直线距离作为排序依据
- 必须使用道路图上 Dijkstra 最短路径距离
- 排序使用自己实现的排序算法

### 6.2 辅助函数

- `validate_facilities_same_map(facilities, map_id)` — 确保设施都属于同一 map
- `extract_path_coordinates(graph, path)` — 提取路径坐标列表

---

## 7. 复杂度分析

| 算法 | 时间复杂度 | 空间复杂度 | 说明 |
|------|-----------|-----------|------|
| Graph 构建 | O(V + E) | O(V + E) | 筛选 map_id + 邻接表构建 |
| 快速排序 | O(N log N) | O(log N) | Lomuto 分区 |
| 归并排序 | O(N log N) | O(N) | 稳定，用于多键排序 |
| 堆排序 | O(N log N) | O(1) | 原地建堆 |
| Top-K (堆) | O(N log K) | O(K) | 自行实现堆 |
| Top-K (快速选择) | O(N) 期望 | O(log N) | 分治选择 |
| 线性搜索 | O(N) | O(1) | 中文关键词匹配 |
| 哈希搜索 | O(1) | O(N) | 预处理哈希索引 |
| Dijkstra | O(V²) | O(V) | 小图，线性扫描未访问节点 |
| 附近查询 | O(F × V²) | O(V) | F 为候选设施数，每个设施一次 Dijkstra |
| 多点路线 (TSP 贪心) | O(T × V²) | O(V) | T 为目标点数，贪心迭代 |

其中 V 为节点数（≤ 40），E 为边数（≤ 102），N 为数据规模（200+）。

---

## 8. 实现状态

| 文件 | 状态 | 测试 |
|------|------|------|
| `backend/algorithms/graph.py` | 已实现 | 101 测试全部通过 |
| `backend/algorithms/sorting.py` | 已实现 | 同上 |
| `backend/algorithms/search.py` | 已实现 | 同上 |
| `backend/algorithms/topk.py` | 已实现 | 同上 |
| `backend/algorithms/dijkstra.py` | 已实现 | 同上 |
| `backend/algorithms/nearby.py` | 已实现 | 同上 |

核心算法约束全部满足：
- 不依赖 networkx / osmnx
- Top-K 不用完整排序后切片
- 附近查询基于道路距离（非直线距离）
- 所有排序算法自行实现
