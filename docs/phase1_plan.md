# Phase 1 实施计划

## 阶段概述

Phase 1 是项目从设计到实现的完整过程，分为 4 个子步骤。

---

## 第 1 步：生成符合课程要求的数据集 ✅

**状态**：已完成
**交付物**：

- [x] `data/destinations.json` — **217** 目的地 (30 校园 + 187 景区)
- [x] `data/internal_maps.json` — **3** 个地图模板 (CAMPUS, SCENIC, MIXED)
- [x] `data/internal_nodes.json` — **112** 节点，每地图 22 实体节点
- [x] `data/internal_edges.json` — **284** 条边，所有图连通
- [x] `data/facilities.json` — **52** 设施，**12** 种类别
- [x] `data/users.json` — **12** 用户
- [x] `data/indoor_graphs.json` — **1** 室内建筑 Demo
- [x] `backend/scripts/generate_seed_data.py` — 数据生成脚本
- [x] `backend/scripts/validate_data.py` — 数据校验脚本（4228 checks passed）
- [x] `docs/data_validation_report.md` — 校验报告

**数据生成方式**：
```bash
python backend/scripts/generate_seed_data.py
```

**数据校验方式**：
```bash
python backend/scripts/validate_data.py
```

**要点**：
- 目的地覆盖北京 30 所高校 + 187 热门景区
- 每个目的地通过 internal_map_id 复用 3 套内部地图模板
- 节点经纬度在对应地图中心附近（北邮周边 / 故宫周边 / 颐和园周边）
- 边数据按要求配置 congestion、speed、allowed_transport
- 校园图无 sightseeing_car，景区图无 bike，混合图均可
- 所有内部地图连通

---

## 第 2 步：实现核心算法 ✅

**状态**：已完成
**交付物**：

- [x] `backend/algorithms/graph.py` — 邻接表图（Graph 类 + load_graph_from_data / load_graph_from_files）
- [x] `backend/algorithms/sorting.py` — 快速排序 / 归并排序 / 堆排序 / 多键排序
- [x] `backend/algorithms/search.py` — 线性查找 / 精确查找 / 哈希索引 / 关键词过滤 / 字段过滤
- [x] `backend/algorithms/topk.py` — Top-K 堆算法 + 快速选择算法
- [x] `backend/algorithms/dijkstra.py` — Dijkstra 最短路径（4 种权函数 + 多点贪心 TSP 近似）
- [x] `backend/algorithms/nearby.py` — 道路距离附近查询
- [x] `tests/conftest.py` — pytest fixtures（加载所有数据文件）
- [x] `tests/test_algorithms/test_graph.py` — Graph 测试
- [x] `tests/test_algorithms/test_sorting.py` — 排序算法测试
- [x] `tests/test_algorithms/test_search.py` — 查找算法测试
- [x] `tests/test_algorithms/test_topk.py` — Top-K 测试
- [x] `tests/test_algorithms/test_dijkstra.py` — Dijkstra + 多点路线测试
- [x] `tests/test_algorithms/test_nearby.py` — 附近查询测试

**测试结果**：`pytest tests/test_algorithms -q` → **101 passed**

**实现要点**：
- 所有核心算法自行实现，不依赖 networkx / osmnx / heapq
- Top-K 使用小顶堆维护大小为 K 的堆，不用完整排序后切片
- 附近设施查询使用 Dijkstra 道路距离排序，不用直线距离
- Dijkstra 返回完整 segments（含 congestion、ideal_speed、real_speed、time）
- 校园图支持 walk/bike；景区图支持 walk/sightseeing_car；混合图三者均可

---

## 第 3 步：实现后端服务和路由 ✅

**状态**：已完成
**交付物**：

- [x] `backend/services/data_loader.py` — 统一 JSON 数据加载 + 内存缓存
- [x] `backend/services/recommendation_service.py` — 推荐服务（Top-K + 搜索 + 过滤 + 兴趣推荐）
- [x] `backend/services/route_service.py` — 路线规划服务（4 种策略 + 多点 TSP + 交通校验）
- [x] `backend/services/nearby_service.py` — 场所查询服务（道路距离排序 + 类别/关键词过滤）
- [x] `backend/services/indoor_service.py` — 室内导航服务（简单 Demo）
- [x] `backend/routes/recommendation_routes.py` — 推荐 API 路由（7 个端点）
- [x] `backend/routes/route_routes.py` — 路线 API 路由（6 个端点）
- [x] `backend/routes/nearby_routes.py` — 场所 API 路由（5 个端点）
- [x] `backend/routes/indoor_routes.py` — 室内 API 路由（2 个端点）
- [x] `backend/app.py` — Flask 应用入口（CORS + 蓝图注册 + 错误处理 + health/stats）
- [x] `tests/test_services/test_recommendation_service.py` — 推荐服务测试
- [x] `tests/test_services/test_route_service.py` — 路线服务测试
- [x] `tests/test_services/test_nearby_service.py` — 场所服务测试
- [x] `tests/test_routes/test_api_basic.py` — API 集成测试

**测试结果**：
- `pytest tests/test_algorithms -q` → **101 passed**
- `pytest tests/test_services -q` → **37 passed**
- `pytest tests/test_routes -q` → **24 passed**
- Total: **162 passed**

**实现要点**：
- 所有 API 通过 destination_id 限定 internal_map_id，路线不跨地图
- 交通工具校验：campus 拒绝 sightseeing_car，attraction 拒绝 bike
- 附近设施排序基于 Dijkstra 道路距离，非直线距离
- 所有推荐/排序/搜索调用第 2 步自定义算法
- 全局错误处理：ValueError → 400，FileNotFoundError → 500

---

## 第 4 步：实现前端页面 ✅

**状态**：已完成
**交付物**：

- [x] `frontend/index.html` — 首页导航
- [x] `frontend/recommendation.html` — 旅游推荐页
- [x] `frontend/route_planning.html` — 路线规划页（Leaflet 地图）
- [x] `frontend/nearby.html` — 场所查询页
- [x] `frontend/indoor_navigation.html` — 室内导航 Demo
- [x] `frontend/css/style.css` — 统一样式
- [x] `frontend/js/api.js` — API 调用封装（PathPalAPI 命名空间）
- [x] `frontend/js/map.js` — Leaflet 地图交互（PathPalMap 命名空间）
- [x] `frontend/js/index.js` — 首页统计加载
- [x] `frontend/js/recommendation.js` — 推荐页面交互
- [x] `frontend/js/route_planning.js` — 路线规划交互 + 地图渲染
- [x] `frontend/js/nearby.js` — 场所查询交互 + 地图渲染
- [x] `frontend/js/indoor_navigation.js` — 室内导航交互
- [x] `backend/scripts/check_frontend_files.py` — 前端文件检查脚本

**启动方式**：
```bash
# 终端 1：后端
cd backend && python app.py

# 终端 2：前端
cd frontend && python -m http.server 8000

# 访问 http://127.0.0.1:8000
```

---

## 第 4.5 步：测试

**预计耗时**：第 4.5 步（可与前端并行）
**交付物**：

- [x] `tests/conftest.py` — pytest fixtures
- [x] `tests/test_algorithms/` — 算法单元测试（101 tests）
- [ ] `tests/test_models/` — 模型测试
- [x] `tests/test_services/` — 服务测试（37 tests）
- [x] `tests/test_routes/` — 路由测试（24 tests）

---

## 质量检查清单

- [x] 所有 API 返回正确格式
- [x] Dijkstra 结果可验证（小图手动计算）
- [x] Top-K 不使用完整排序
- [x] 附近查询基于道路距离（非直线距离）
- [x] bike 不能走 sightseeing_car 道路
- [x] sightseeing_car 不能走 bike 道路
- [x] 跨 internal_map_id 查询被拒绝（通过 destination_id 限定）
- [x] Leaflet 正确渲染内部地图（已完成）
- [x] 200+ 条道路边验证通过
- [x] 50+ 设施 / 10+ 类别验证通过
- [x] 10+ 用户数据验证通过

---

## 第 5 步：端到端验收与文档 ✅

**状态**：已完成
**交付物**：

- [x] `backend/scripts/e2e_smoke_check.py` — E2E smoke 自动化检查脚本
- [x] `docs/e2e_acceptance_report.md` — 端到端手动验收记录
- [x] `docs/test_report.md` — 测试报告（覆盖/结果/说明）
- [x] `docs/phase1_completion_report.md` — Phase 1 阶段完成报告
- [x] `docs/demo_script.md` — 答辩演示脚本（含常见追问）
- [x] `docs/frontend_usage.md` — 前端使用指南
- [x] `requirements.txt` — 依赖清单
- [x] `README.md` — 更新启动流程、测试命令、文档索引、开发阶段

**测试结果汇总**：
- `validate_data.py` → 4228/4228 passed
- `pytest tests/test_algorithms -q` → 101 passed
- `pytest tests/test_services -q` → 37 passed
- `pytest tests/test_routes -q` → 24 passed
- `check_frontend_files.py` → All passed
- `e2e_smoke_check.py` → 需后端运行后执行

**Phase 1 总结**：全部 5 步完成，三个核心模块（旅游推荐、路线规划、场所查询）+ 室内导航 Demo 均可验收演示。
