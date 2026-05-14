# 地图数据策略 (Map Data Strategy)

## 设计动机

PathPal 的路线规划和场所查询发生在景区/校园**内部道路图**中，不是城市级外部导航。

为了在数据结构课程设计中体现真实地理数据的应用价值，同时避免"模拟路线叠加真实地图瓦片"导致的视觉误导，采用了**真实地图 + 抽象模板**的混合策略。

---

## 地图分类

### 真实地图 (Real Maps)

| map_id | 名称 | 类型 | 数据来源 |
|--------|------|------|----------|
| MAP_BUPT_REAL | 北京邮电大学真实校园内部图 | campus | OpenStreetMap |
| MAP_BNU_REAL | 北京师范大学真实校园内部图 | campus | OpenStreetMap |
| MAP_SCENIC_REAL | 天坛公园真实内部图 | attraction | OpenStreetMap |

**特征**：
- `is_real_map: true`
- `show_tile: true`
- `source: "openstreetmap_vector"`
- 节点、边、设施基于真实地理位置
- 前端加载 OpenStreetMap 瓦片叠加路线

**绑定关系**：
- DEST_001 (北京邮电大学) → MAP_BUPT_REAL
- DEST_007 (北京师范大学) → MAP_BNU_REAL
- DEST_032 (天坛公园) → MAP_SCENIC_REAL

### OSM 矢量模板 (OSM Vector Templates)

| map_id | 名称 | 类型 | 数据来源 |
|--------|------|------|----------|
| MAP_CAMPUS_OSM | 清华大学 OSM 校园模板 | campus | OpenStreetMap |
| MAP_SCENIC_OSM | 颐和园 OSM 景区模板 | attraction | OpenStreetMap |

**特征**：
- 基于真实 OSM 矢量数据
- 供多个目的地复用（类似抽象模板，但使用真实地理位置）
- 学校类目的地（除北邮、北师大外）→ MAP_CAMPUS_OSM
- 景区类目的地（除天坛外）→ MAP_SCENIC_OSM

### 抽象模板 (Simulated Templates)

| map_id | 名称 | 类型 |
|--------|------|------|
| MAP_CAMPUS_001 | 校园标准模板 | campus |
| MAP_SCENIC_001 | 景区标准模板 | attraction |
| MAP_MIXED_001 | 综合园区模板 | mixed |

**特征**：
- `is_real_map: false`
- `show_tile: false`
- `source: "generated_template"`
- 节点、边、设施为模拟生成
- 前端**不**加载 OSM 瓦片，使用浅色空白背景
- 页面显示提示："当前目的地复用抽象内部地图模板，不叠加真实地图瓦片"

**绑定关系**：
- 28 个 campus 目的地 → MAP_CAMPUS_OSM（OSM 模板）
- 117 个 attraction 目的地 → MAP_SCENIC_OSM（OSM 模板）
- 69 个 attraction 目的地 → MAP_MIXED_001（抽象模板）

> **备注**：MAP_CAMPUS_001 和 MAP_SCENIC_001 作为备用抽象模板保留，当前无目的地绑定。

---

## 为什么不全部使用真实地图？

1. **工作量**：为 217 个目的地逐一爬取/整理真实地图不现实
2. **课程设计允许**：课程要求中明确指出"景区和校园内部可以一致"，即允许复用内部地图模板
3. **OSM 数据丰富度**：部分知名景区/校园在 OSM 上有足够丰富的内部道路数据
4. **展示效果**：真实地图展示核心能力，OSM 矢量模板兼顾数据规模要求

---

## 前端展示逻辑

### show_tile = true（真实地图）
- Leaflet 正常加载 OpenStreetMap 瓦片
- 地图中心设置为真实地理坐标
- 绘制真实内部路线
- 显示标签："真实 OSM 内部道路图"

### show_tile = false（抽象模板）
- 不加载 OpenStreetMap 瓦片
- 使用 Leaflet 空白背景
- 仍然绘制节点、边、路线和设施
- 显示标签："抽象内部地图模板"

### 实现方式
- `frontend/js/map.js`：`createMap()` 接受 `showTile` 参数，通过 `setTileVisible()` 动态控制瓦片
- `frontend/js/route_planning.js` / `nearby.js`：从 `/api/route/nodes` 或 `/api/nearby` 响应中获取 `internal_map` 元数据，调用 `updateMapForMeta()` 更新地图
- HTML 页面添加 `#map-source-note` 元素显示地图来源提示

---

## 课程要求对应

| 要求 | 实现 |
|------|------|
| 建立景区和校园内部道路图 | 5 个内部地图模板（2 真实 + 3 抽象） |
| 边数 >= 200 | 416 条边 |
| 节点 >= 90 | 164 个节点 |
| 尽量接近真实 | 2 个 OSM 真实地图模板 |
| 景区和校园内部可以一致 | 3 个抽象模板供复用 |
| 不做城市级外部导航 | 所有路线仅在 internal_map_id 内部 |
| 核心算法自行实现 | Dijkstra / Top-K / Sort / Search 全部自写 |

---

## 新增 API

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/internal-maps | GET | 列出所有内部地图（含 is_real_map / show_tile / center） |
| /api/internal-maps/<map_id> | GET | 获取指定内部地图详情 |
| /api/destinations/<destination_id>/map-layers | GET | 获取目的地的完整地图图层（节点+边+设施+元数据） |

`/api/route/nodes` 和 `/api/nearby` 响应中新增 `internal_map` 字段，方便前端判断是否显示瓦片。

---

## 前端分层管理说明

map.js 使用三层图层组：

| 图层 | Leaflet LayerGroup | 职责 | 清空时机 |
|------|-------------------|------|---------|
| baseLayer | L.layerGroup | 内部道路网络（所有节点+边+设施） | 切换目的地时清空 |
| routeLayer | L.layerGroup | 当前规划路线 + 分段 | 重新规划时清空 |
| markerLayer | L.layerGroup | 起点/终点标记 | 重新规划时清空 |

- `clearRouteLayers()` 和 `clearMarkerLayers()` 不会影响 baseLayer，保证基础路网始终可见
- `drawBaseNetwork()` 根据 road_type 和 allowed_transport 用不同颜色/样式绘制所有道路边
- 节点按 type（gate/scenic_spot/building/intersection）用不同大小和颜色标记
- 设施按 category 用不同颜色的小圆点标记，带 popup

### show_tile = true（真实地图）时
- Leaflet 加载 OpenStreetMap 瓦片
- 基础路网叠加在瓦片之上（半透明边缘和节点）
- 路线规划结果用高亮线覆盖
- 页面标注："真实 OSM 内部道路图"

### show_tile = false（抽象模板）时
- 不加载 OSM 瓦片，背景为浅灰色
- 绘制完整内部道路网络（所有节点、边、设施）
- 普通道路边用浅灰线，bike 边用绿色虚线，sightseeing_car 边用橙色虚线
- 路线规划结果用高亮线叠加在基础网络上
- 页面标注："抽象内部地图模板：该目的地复用课程设计内部道路模板，不叠加真实地图瓦片"
