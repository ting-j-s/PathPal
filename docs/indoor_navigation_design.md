# 室内导航设计文档

## 1. 功能目标

在 Phase 1 室内导航 Demo 基础上，升级为较完整的课程设计功能：

- 模拟教学楼和景区展馆的室内多层结构
- 支持大门到电梯的导航
- 支持楼层间电梯/楼梯换乘导航
- 支持楼层内到房间的导航
- 使用简单 SVG 拓扑图展示室内节点和边

## 2. 数据结构设计

室内数据存放在 `data/indoor_graphs.json`，顶层结构：

```json
{
  "indoor_maps": [
    { "building_id": "...", ... },
    { "building_id": "...", ... }
  ]
}
```

### 2.1 Building Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| building_id | string | 唯一标识 |
| building_name | string | 建筑名称 |
| building_type | string | campus_building 或 scenic_exhibition |
| destination_id | string | 关联目的地（可选） |
| description | string | 建筑描述 |
| floors | [int] | 楼层列表 |
| nodes | [node] | 节点数组 |
| edges | [edge] | 边数组 |

### 2.2 Node Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 唯一节点标识 |
| name | string | 节点名称（如"教学楼大门"） |
| floor | int | 所属楼层 |
| type | string | 节点类型（见下表） |
| x | int | SVG 局部横坐标 |
| y | int | SVG 局部纵坐标 |

**节点类型**：

| type | 说明 |
|------|------|
| entrance | 建筑入口 |
| lobby | 大厅 |
| elevator | 电梯间 |
| stairs | 楼梯间 |
| corridor | 走廊节点 |
| classroom | 教室 |
| office | 办公室 |
| restroom | 卫生间 |
| service_point | 服务点（值班室、商店等） |
| exhibition_hall | 展厅 |
| exit | 出口 |

### 2.3 Edge Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 唯一边标识 |
| from | string | 起始节点 ID |
| to | string | 终止节点 ID |
| distance | float | 距离（米） |
| type | string | 边类型 |

**边类型**：

| type | 说明 | 用途 |
|------|------|------|
| corridor | 走廊 | 同层节点间通行 |
| elevator | 电梯 | 跨楼层垂直通行 |
| stairs | 楼梯 | 跨楼层垂直通行 |
| doorway | 门 | 入口到大厅等过渡 |

## 3. 校园建筑数据设计：BUILDING_BUPT_TEACHING

- **名称**：北邮教学楼
- **类型**：campus_building
- **规模**：4 层，40 节点，48 边

**1F**（10 节点）：大门 → 大厅 → 东/西走廊 → 电梯、楼梯、值班室、卫生间、教室101、教室102

**2F**（10 节点）：电梯、楼梯 → 东/西走廊 → 卫生间、教室201–203、办公室201–202

**3F**（10 节点）：电梯、楼梯 → 走廊 → 卫生间、教室301–302、实验室301、办公室301–302

**4F**（10 节点）：电梯、楼梯 → 走廊 → 卫生间、教室401–402、会议室401、办公室401–402

**跨层连接**：3 条电梯边 + 3 条楼梯边，连接各层电梯/楼梯节点。

## 4. 景区展馆数据设计：BUILDING_TIANTAN_EXHIBITION

- **名称**：天坛展馆
- **类型**：scenic_exhibition
- **规模**：3 层，27 节点，35 边

**1F**（9 节点）：展馆入口 → 大厅 → 服务台、文创商店、电梯、楼梯 → 展厅1–2、卫生间

**2F**（9 节点）：电梯、楼梯 → 东/西走廊 → 展厅3–4、休息区、观景点、卫生间

**3F**（9 节点）：电梯、楼梯 → 走廊 → 展厅5–6、管理办公室、出口指引点、卫生间

**跨层连接**：2 条电梯边 + 2 条楼梯边。

## 5. 室内图邻接表

Dijkstra 算法使用无向图邻接表。每条 `corridor` 边连接同层两个节点，在邻接表中双向添加：

```
adj[u].append((v, edge))
adj[v].append((u, edge))
```

每条 `elevator` 边连接不同层的电梯节点，实现跨层通行。`stairs` 边连接不同层的楼梯节点。

## 6. Dijkstra 最短路径

算法实现：`backend/algorithms/indoor_dijkstra.py`

```python
def indoor_dijkstra(building, start_id, end_id):
    # 1. 构建无向邻接表
    # 2. 标准 Dijkstra，权重 = edge.distance
    # 3. 回溯路径，收集节点和边
    # 4. 生成步骤描述和楼层分组
    return {
        "reachable": bool,
        "path": [node_id, ...],
        "distance": float,
        "nodes": [...],
        "edges": [...],
        "steps": [...],
        "floor_paths": {floor: [...]},
    }
```

- 时间复杂度：O((V+E) log V)
- 空间复杂度：O(V+E)
- 边权 = distance（米）
- 图默认无向

## 7. 步骤生成逻辑

`_generate_steps(nodes, edges)` 根据 `edge.type` 生成中文步骤：

| edge.type | 步骤格式 |
|-----------|---------|
| corridor | 沿走廊前往{目标}({楼层}F)（{}米） |
| elevator | 乘电梯从{楼层}F到{楼层}F（{}米） |
| stairs | 走楼梯从{楼层}F到{楼层}F（{}米） |
| doorway | 通过门口前往{目标}（{}米） |

## 8. 前端 SVG 拓扑展示

`renderFloorGraphs(building, routeResult)` 为每层生成独立 SVG panel：

- 节点：圆形，按类型着色（蓝=入口，绿=电梯，橙=楼梯，黄=教室，紫=办公室，红=出口等）
- 边：灰色细线（corridor）、虚线（elevator/stairs）
- 路径高亮：蓝色粗线
- 节点名称：文本标注在节点右侧

## 9. 当前限制

- 暂不接入室外路线（室内导航独立运行）
- 暂不做真实楼层平面图（使用简单 SVG 拓扑）
- 暂不做无障碍策略（只做最短距离）
- 暂不做最少换层策略
- 暂不做室内-室外联动
- 暂不连接数据库（使用 JSON 文件）

## 10. API 列表

| Method | Endpoint | 说明 |
|--------|----------|------|
| GET | /api/indoor/buildings | 建筑列表 |
| GET | /api/indoor/buildings/&lt;id&gt; | 建筑详情 |
| GET | /api/indoor/nodes?building_id=&floor= | 节点列表 |
| GET | /api/indoor/floors?building_id= | 楼层信息 |
| GET | /api/indoor/route?building_id=&start=&end= | 室内路径 |
