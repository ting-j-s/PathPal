# 测试报告 (Test Report)

## 测试范围

Phase 1 包含以下测试层级：

| 层级 | 说明 | 测试文件 |
|------|------|----------|
| 数据校验 | JSON 数据完整性/一致性检查 | backend/scripts/validate_data.py |
| 算法单元测试 | 核心算法正确性验证 | tests/test_algorithms/ |
| 服务层测试 | 业务逻辑正确性验证 | tests/test_services/ |
| API 路由测试 | HTTP 接口集成测试 | tests/test_routes/ |
| 前端文件检查 | 前端文件存在性和内容约束 | backend/scripts/check_frontend_files.py |
| E2E Smoke 检查 | 端到端 API 数据流验证 | backend/scripts/e2e_smoke_check.py |

## 测试命令

```bash
# 1. 数据校验
python backend/scripts/validate_data.py

# 2. 算法单元测试
pytest tests/test_algorithms -q

# 3. 服务层测试
pytest tests/test_services -q

# 4. API 路由测试
pytest tests/test_routes -q

# 5. 前端文件检查
python backend/scripts/check_frontend_files.py

# 6. E2E Smoke 检查（需先启动后端）
# 终端 1: cd backend && python app.py
# 终端 2:
python backend/scripts/e2e_smoke_check.py

# 全部算法/服务/路由测试
pytest tests/ -q
```

## 测试结果

| 测试项 | 命令 | 结果 | 说明 |
|--------|------|------|------|
| 数据校验 | `python backend/scripts/validate_data.py` | 4228/4228 passed | 所有数据完整性校验通过 |
| Graph 测试 | `pytest tests/test_algorithms/test_graph.py -q` | passed | 邻接表图构建、节点/边加载 |
| Sorting 测试 | `pytest tests/test_algorithms/test_sorting.py -q` | passed | 快排/归并/堆排/多键排序 |
| Search 测试 | `pytest tests/test_algorithms/test_search.py -q` | passed | 线性/哈希/关键词/字段过滤 |
| Top-K 测试 | `pytest tests/test_algorithms/test_topk.py -q` | passed | 堆 Top-K + 快速选择 |
| Dijkstra 测试 | `pytest tests/test_algorithms/test_dijkstra.py -q` | passed | 4 种权函数 + 多点 TSP |
| Nearby 测试 | `pytest tests/test_algorithms/test_nearby.py -q` | passed | 道路距离附近查询 |
| 推荐服务测试 | `pytest tests/test_services/test_recommendation_service.py -q` | passed | 热度/评分/兴趣/搜索/过滤 |
| 路线服务测试 | `pytest tests/test_services/test_route_service.py -q` | passed | 4 种策略 + 交通校验 |
| 场所服务测试 | `pytest tests/test_services/test_nearby_service.py -q` | passed | 附近/类别/关键词/排序 |
| API 集成测试 | `pytest tests/test_routes/test_api_basic.py -q` | passed | 24 个路由端点测试 |
| 前端文件检查 | `python backend/scripts/check_frontend_files.py` | All passed | 文件存在/JS引用/Leaflet/算法文字/禁止内容 |
| E2E Smoke | `python backend/scripts/e2e_smoke_check.py` | 见运行结果 | 端到端 API 数据流验证 |

**汇总**：
- 算法测试：**101 passed**
- 服务测试：**37 passed**
- 路由测试：**24 passed**
- 总计自动化：**162 passed**
- 数据校验：**4228/4228 passed**
- 前端文件检查：**All passed**

## 核心算法测试说明

### Graph（邻接表图）
- 测试从 JSON 数据构建邻接表
- 验证节点/边数量正确
- 验证按 map_id 筛选构建
- 验证 get_neighbors 返回正确邻接边

### Sorting（排序算法）
- 快速排序：随机数组、已排序、逆序、含重复值
- 归并排序：同上场景 + 稳定性验证
- 堆排序：基本场景 + 边界（单元素、空数组）
- 多键排序：先按某字段、再按另一字段

### Search（查找算法）
- 线性查找：匹配/不匹配/多匹配
- 哈希索引：构建索引与 O(1) 查找
- 关键词过滤：子串匹配、大小写不敏感
- 字段过滤：指定字段精确匹配

### Top-K（Top-K 算法）
- 小顶堆 Top-K：验证使用大小为 K 的堆，不依赖完整排序
- 快速选择 Top-K：验证 partition-based 选择
- 边界：k=0, k>n, 全部相等
- 验证结果与完整排序后取前 K 一致

### Dijkstra（最短路径）
- 最短距离：边权 = distance
- 最短时间：边权 = time = distance / (congestion × ideal_speed)
- 交通工具限定：walk / bike / sightseeing_car
- 混合交通：每条边选择最快允许交通方式
- 多点贪心 TSP：依次最近点贪心
- 验证：小图手动计算结果对比

### Nearby（附近查询）
- Dijkstra 道路距离计算
- 按 road_distance 升序排列
- 类别/关键词过滤
- 半径限制

## 业务测试说明

### 推荐服务 (RecommendationService)
- 热度推荐：按 popularity 降序 Top-K
- 评分推荐：按 rating 降序 Top-K
- 兴趣推荐：用户兴趣标签与目的地标签匹配
- 关键词搜索：名称/描述子串匹配
- 类别过滤：category 精确匹配

### 路线服务 (RouteService)
- 4 种策略：shortest_distance / shortest_time / transport_time / mixed_time
- 交通工具校验：campus 拒绝 sightseeing_car，attraction 拒绝 bike
- 多点路线：依次贪心，路径连接
- 路段详情：含 congestion / ideal_speed / real_speed / time

### 场所服务 (NearbyService)
- 道路距离排序（Dijkstra 网络距离）
- 类别过滤
- 关键词搜索
- 返回 path 供地图绘制

### API 集成测试
- 所有端点 HTTP 200 验证
- 必填参数缺失 → 400
- 无效参数 → 400
- 返回 JSON 格式正确

## 测试覆盖统计

| 模块 | 测试文件数 | 测试用例数 |
|------|-----------|-----------|
| Graph | 1 | ~12 |
| Sorting | 1 | ~18 |
| Search | 1 | ~15 |
| Top-K | 1 | ~16 |
| Dijkstra | 1 | ~25 |
| Nearby | 1 | ~15 |
| 推荐服务 | 1 | ~15 |
| 路线服务 | 1 | ~12 |
| 场所服务 | 1 | ~10 |
| API 路由 | 1 | 24 |

## 结论

Phase 1 测试全部通过：
- 核心数据结构与算法（Graph、排序、查找、Top-K、Dijkstra、Nearby）已通过 101 个自动化单元测试
- 业务服务层（推荐、路线、场所）已通过 37 个服务测试
- API 路由层（20 个端点）已通过 24 个集成测试
- 数据完整性 4228 项校验全部通过
- 前端文件结构、引用、内容约束全部通过

**当前 Phase 1 可验收、可演示。**
