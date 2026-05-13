# 数据校验报告 (Data Validation Report)

## 生成时间

2026-05-12

## 数据规模统计

| 数据项 | 数量 | 要求 | 状态 |
|--------|------|------|------|
| Destinations | 217 | >= 200 | OK |
| — Campus | 30 | — | — |
| — Attraction | 187 | — | — |
| Internal Maps | 3 | >= 3 | OK |
| Internal Nodes | 112 | >= 90 (建议) | OK |
| Internal Edges | 284 | >= 200 | OK |
| Facilities | 52 | >= 50 | OK |
| Facility Categories | 12 | >= 10 | OK |
| Users | 12 | >= 10 | OK |
| Indoor Buildings | 1 | >= 1 | OK |

## 每个 internal_map_id 详情

| Map ID | Type | Nodes | Entity Nodes | Edges | Facilities |
|--------|------|-------|-------------|-------|------------|
| MAP_CAMPUS_001 | campus | 37 | 22 | 90 | 22 |
| MAP_SCENIC_001 | attraction | 36 | 22 | 92 | 13 |
| MAP_MIXED_001 | mixed | 39 | 22 | 102 | 17 |
| **Total** | — | **112** | **66** | **284** | **52** |

## 校验项目

### 1. Destinations 校验
- [x] 数量 >= 200 (217)
- [x] ID 唯一
- [x] type 仅为 campus 或 attraction
- [x] 每个 destination 有 internal_map_id
- [x] internal_map_id 在 internal_maps.json 中存在
- [x] campus 仅绑定 MAP_CAMPUS_001 或 MAP_MIXED_001
- [x] attraction 仅绑定 MAP_SCENIC_001 或 MAP_MIXED_001
- [x] popularity > 0
- [x] rating 在 (0, 5.0]

### 2. Internal Maps 校验
- [x] 数量 >= 3
- [x] map_id 唯一
- [x] 包含 MAP_CAMPUS_001、MAP_SCENIC_001、MAP_MIXED_001
- [x] 每个 map type 正确

### 3. Internal Nodes 校验
- [x] ID 唯一
- [x] 每个 map_id 存在
- [x] 每个 map_id 实体节点 >= 20 (均为 22)
- [x] 每个节点有 latitude 和 longitude

### 4. Internal Edges 校验
- [x] 总边数 >= 200 (284)
- [x] ID 唯一
- [x] from/to 节点存在
- [x] from/to 节点属于同一 map_id
- [x] edge.map_id 与 from/to 节点 map_id 一致
- [x] distance > 0
- [x] 0 < congestion <= 1
- [x] allowed_transport 非空
- [x] campus 图无 sightseeing_car
- [x] scenic 图无 bike

### 5. Facilities 校验
- [x] 数量 >= 50 (52)
- [x] ID 唯一
- [x] 类别数 >= 10 (12)
- [x] map_id 存在
- [x] linked_node_id 存在
- [x] linked_node_id 对应节点的 map_id == facility.map_id

### 6. Users 校验
- [x] 数量 >= 10 (12)
- [x] ID 唯一
- [x] interests 非空
- [x] favorite_categories 非空
- [x] preferred_tags 非空

### 7. Indoor Graphs 校验
- [x] 至少 1 个 building
- [x] 有 nodes 和 edges
- [x] 室内边 from/to 存在

### 8. 连通性校验（BFS 自行实现）
- [x] MAP_CAMPUS_001: connected (37/37)
- [x] MAP_SCENIC_001: connected (36/36)
- [x] MAP_MIXED_001: connected (39/39)

## 校验结果

```
Validation Summary: 384969/384969 passed
  All validation checks passed.
```

**所有课程硬性数据要求均已满足。**
