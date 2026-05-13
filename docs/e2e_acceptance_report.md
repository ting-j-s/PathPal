# 端到端验收报告 (E2E Acceptance Report)

## 验收环境

| 项目 | 值 |
|------|-----|
| Python 版本 | 3.x |
| 后端框架 | Flask |
| 后端地址 | http://127.0.0.1:5000 |
| 前端地址 | http://127.0.0.1:8000 |
| 前端服务器 | Python http.server |
| 浏览器 | Chrome / Edge / Firefox（推荐最新版） |

## 启动方式

```bash
# 终端 1：后端
cd backend
python app.py

# 终端 2：前端
cd frontend
python -m http.server 8000
```

访问地址：http://127.0.0.1:8000

## 数据规模（来自 /api/stats）

| 数据项 | 数量 |
|--------|------|
| destinations | 217 |
| internal_maps | 3 |
| internal_nodes | 112 |
| internal_edges | 284 |
| facilities | 52 |
| facility_categories | 12 |
| users | 12 |
| indoor_buildings | 1 |

---

## 页面验收记录

### 1. 首页 (index.html)

| 验收项 | 操作步骤 | 期望结果 | 实际结果 | 状态 |
|--------|----------|----------|----------|------|
| 页面打开 | 访问 http://127.0.0.1:8000 | 显示 PathPal 首页，含导航栏 | 正常显示 | PASS |
| Stats 加载 | 页面自动加载 /api/stats | 显示 7 项数据统计卡片 | 加载 217 destinations / 3 maps / 112 nodes / 284 edges / 52 facilities / 12 categories / 12 users | PASS |
| 导航链接 | 点击导航栏"旅游推荐" | 跳转到 recommendation.html | 正常跳转 | PASS |
| 导航链接 | 点击导航栏"路线规划" | 跳转到 route_planning.html | 正常跳转 | PASS |
| 导航链接 | 点击导航栏"场所查询" | 跳转到 nearby.html | 正常跳转 | PASS |
| 导航链接 | 点击导航栏"室内导航" | 跳转到 indoor_navigation.html | 正常跳转 | PASS |
| 算法说明 | 查看页面下方算法亮点区域 | 显示 Top-K、Dijkstra、道路距离等 | 包含算法说明 | PASS |
| 不做功能标注 | 查看"明确不做"区域 | 标注不做日记、美食、登录等 | 使用 warning tag 展示 | PASS |

### 2. 旅游推荐页 (recommendation.html)

| 验收项 | 操作步骤 | 期望结果 | 实际结果 | 状态 |
|--------|----------|----------|----------|------|
| 热度 Top-10 | 点击"热度 Top-10 推荐" | 返回热度最高的 10 个目的地 | 返回 Top-10，按 popularity 降序 | PASS |
| 评分 Top-10 | 点击"评分 Top-10 推荐" | 返回评分最高的 10 个目的地 | 返回 Top-10，按 rating 降序 | PASS |
| 兴趣推荐 | 输入 USER_001，点击"兴趣推荐" | 返回个性化匹配 Top-10 | 返回含 interest_score 和 recommendation_reason 的结果 | PASS |
| 关键词搜索 | 输入"北京"，排序选"按评分"，点击搜索 | 返回名称包含"北京"的目的地 | 返回匹配结果 | PASS |
| 关键词搜索 | 输入"大学" | 返回名称包含"大学"的目的地 | 返回匹配结果 | PASS |
| 类别过滤 | 输入"park"，点击"类别过滤" | 返回 park 类别目的地 | 返回按类别过滤的结果 | PASS |
| 类型过滤 | 选择"校园"，点击"列出目的地" | 返回所有 campus 类型 | 列表含 campus 标签 | PASS |
| 结果展示 | 查看结果表格 | 包含 name/type/category/popularity/rating/tags | 字段完整 | PASS |
| 算法说明 | 查看算法说明区域 | Top-K Heap / Quick Sort / Linear Search / 兴趣匹配公式 | 算法说明完整 | PASS |

### 3. 路线规划页 (route_planning.html)

| 验收项 | 操作步骤 | 期望结果 | 实际结果 | 状态 |
|--------|----------|----------|----------|------|
| 目的地加载 | 打开页面 | 目的地下拉框加载完成 | 217 个目的地可选 | PASS |
| 节点加载 | 选择"北京邮电大学"(campus) | 内部节点加载 | 显示 MAP_CAMPUS_001 节点 | PASS |
| 交通提示 | 选择 campus 目的地 | 显示 walk/bike 可用，sightseeing_car 不可用 | 提示正确 | PASS |
| 最短距离 | 选起点终点，策略=最短距离，点击规划 | 返回最短距离路径 | path/segments/total_distance/total_time | PASS |
| 最短时间 walk | 策略=最短时间，transport=walk | 返回按时间最短的路径 | 含完整 segments | PASS |
| 最短时间 bike | 策略=最短时间，transport=bike | campus 下 bike 路线正常 | bike 路段显示 | PASS |
| campus-sightseeing_car | transport=sightseeing_car，campus 目的地 | 被拒绝或提示不可用 | 后端返回 400 错误 | PASS |
| 混合交通 campus | 策略=混合交通 | 每条边自动选最快交通 | mixed 结果 | PASS |
| 多目标路线 | 输入途经节点，点击"多目标规划" | 返回多点贪心路线 | 含 waypoints | PASS |
| 景区 sightseeing_car | 选"故宫博物院"(attraction)，transport=sightseeing_car | 路线正常返回 | sightseeing_car 可用 | PASS |
| 景区 bike 拒绝 | 选 attraction，transport=bike | 被拒绝 | 后端返回 400 | PASS |
| Leaflet 地图 | 规划路线后 | 地图显示路线 | polyline 不同颜色（蓝/绿/橙） | PASS |
| 路段详情表 | 规划路线后 | 显示每段 from/to/distance/transport/congestion/ideal_speed/real_speed/time | 完整显示 | PASS |
| 算法说明 | 查看算法说明 | Dijkstra / 邻接表 / real_speed 公式 / mixed 策略 | 完整 | PASS |
| 不做城市导航 | 查看页面标注 | 明确标注不做城市级外部导航 | warning 提示 | PASS |

### 4. 场所查询页 (nearby.html)

| 验收项 | 操作步骤 | 期望结果 | 实际结果 | 状态 |
|--------|----------|----------|----------|------|
| 目的地加载 | 打开页面 | 目的地下拉框加载 | 217 个目的地可选 | PASS |
| 节点加载 | 选 destination | 节点下拉框加载 | 节点列表正确 | PASS |
| 查询全部设施 | 选节点，点击"查询全部" | 返回附近设施按 road_distance 排序 | 排序正确 | PASS |
| 按类别查询 | 选类别如 toilet，点击"按类别查询" | 仅返回该类别设施 | 过滤正确 | PASS |
| 关键词搜索 | 输入关键词如"超市" | 返回匹配设施 | 搜索正常 | PASS |
| 半径过滤 | 设置 radius 参数 | 仅返回范围内设施 | 过滤正确 | PASS |
| road_distance 升序 | 查看结果排序 | 按道路距离从小到大 | 正确 | PASS |
| 查看路径 | 点击某设施的"查看路径" | 在地图上绘制起点到该设施的路径 | Leaflet 路径显示 | PASS |
| 设施标记 | 查看地图 | 绿色标记显示设施 | popup 含名称/类别/道路距离 | PASS |
| 算法说明 | 查看算法说明 | Dijkstra 道路距离 / 不是经纬度直线距离 | 正确标注 | PASS |

### 5. 室内导航 Demo (indoor_navigation.html)

| 验收项 | 操作步骤 | 期望结果 | 实际结果 | 状态 |
|--------|----------|----------|----------|------|
| 页面打开 | 访问 indoor_navigation.html | 正常显示 | 显示 Demo 标注 | PASS |
| 建筑加载 | 页面自动加载 /api/indoor/buildings | 建筑列表 | 加载建筑 | PASS |
| 室内路线 | 选建筑，输入起点终点节点 ID | 返回室内路径 | path/steps 显示 | PASS |
| 步骤详情 | 查询后 | 展示每步详情 | 步骤表格 | PASS |

---

## 约束确认

| 约束 | 确认 |
|------|------|
| 不做城市级外部导航 | 是 — 路线限定在 internal_map_id 内部 |
| 不做跨景区/校园路线 | 是 — 通过 destination_id 限定地图 |
| nearby 使用道路距离排序 | 是 — Dijkstra 网络距离，非直线距离 |
| 不做旅游日记 | 是 — 无日记相关页面或 API |
| 不做美食推荐 | 是 — 无美食相关页面或 API |
| 不做完整登录注册 | 是 — 仅使用 user_id 参数模拟 |
| 不使用数据库 | 是 — 全部 JSON 文件存储 |

---

## 当前已知限制

1. 前端为原生 HTML/CSS/JS，无 React/Vue 框架
2. 地图使用 Leaflet + OpenStreetMap 瓦片展示内部路径，不调用真实导航 API
3. 目的地内部地图使用 3 套模板复用（campus/scenic/mixed）
4. 第一阶段不实现日记、美食、完整登录注册
5. 多点路线使用贪心近似算法，不保证全局最优解
6. 室内导航为 Demo 级别，仅含 1 栋建筑
7. 所有数据存储在 JSON 文件中，无数据库持久化
8. 前端通过 python -m http.server 提供静态服务，后端使用 Flask dev server
