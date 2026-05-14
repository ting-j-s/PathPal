# PathPal（旅伴）

基于智能体的个性化旅游系统的设计与实现 —— 数据结构课程设计项目

## 项目简介

PathPal 是一个基于 Python Flask 的个性化旅游辅助系统。当前阶段聚焦于三个核心功能模块：
景区/校园内部的路线规划、场所查询和目的地推荐。

### 地图数据说明

- **MAP_BUPT_REAL** 和 **MAP_SCENIC_REAL** 是基于 OpenStreetMap 的真实内部道路图模板，前端显示 OSM 瓦片叠加路线
- **MAP_CAMPUS_001**、**MAP_SCENIC_001**、**MAP_MIXED_001** 为抽象内部地图模板，供其他目的地复用，前端不叠加真实瓦片，但绘制完整内部道路网络（节点/边/设施）
- 详见 [地图数据策略](docs/map_data_strategy.md)

### 地图展示策略

| 地图类型 | OSM 瓦片 | 内部道路网络 | 示例目的地 |
|---------|---------|------------|-----------|
| 真实地图 (show_tile=true) | 显示 | 叠加半透明路网 | 北京邮电大学、天坛公园 |
| 抽象模板 (show_tile=false) | 不显示（浅灰背景） | 完整绘制节点/边/设施 | 北京大学、故宫等 215 个 |

## 当前阶段范围

### 已实现功能

| 模块 | 说明 |
|------|------|
| 旅游推荐 | 按热度/评分/用户兴趣推荐目的地 Top-K，支持关键词搜索 |
| 内部路线规划 | 景区/校园内部道路图的最短路径规划（距离/时间/交通/混合策略） |
| 场所查询 | 基于道路距离的附近服务设施查询（洗手间、商店、食堂等） |

### 路线规划策略

- **最短距离**：Dijkstra，边权 = distance
- **最短时间**：Dijkstra，边权 = time = distance / (congestion * ideal_speed)
- **交通工具**：校园支持 walk / bike / mixed；景区支持 walk / sightseeing_car / mixed
- **混合交通**：每条边自动选择最快交通工具

### 明确不做

- 不做旅游日记管理
- 不做旅游日记交流
- 不做美食推荐
- 不做完整登录注册（仅用 user_id 模拟个性化推荐）
- 不做城市级外部导航
- 不做跨景区路线规划
- 不做从用户家到景区大门的外部路线

> **重要**：路线规划和场所查询只发生在"用户已进入某个景区或校园之后"的内部场景中。本项目不是百度/高德地图，不做城市级导航。

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Python Flask |
| 前端 | HTML + CSS + JavaScript（原生） |
| 地图 | Leaflet |
| 数据存储 | JSON 文件 |
| 核心算法 | 自行实现（排序、查找、Dijkstra、Top-K） |
| 测试 | pytest |

## 项目结构

```
PathPal/
├── README.md
├── config.py                     # 全局配置
├── docs/                         # 设计文档
│   ├── requirement_analysis.md   # 需求分析
│   ├── system_design.md          # 系统设计
│   ├── data_structure_design.md  # 数据结构设计
│   ├── algorithm_design.md       # 算法设计
│   ├── api_design.md             # API 设计
│   ├── phase1_plan.md            # 实施计划
│   └── future_extensions.md      # 未来扩展（备忘）
├── backend/                      # 后端代码
│   ├── app.py                    # Flask 应用入口
│   ├── algorithms/               # 核心算法（自行实现）
│   │   ├── graph.py              # 邻接表图
│   │   ├── dijkstra.py           # Dijkstra 最短路
│   │   ├── topk.py               # Top-K 算法
│   │   ├── sorting.py            # 排序算法
│   │   ├── search.py             # 查找算法
│   │   └── nearby.py             # 附近查询
│   ├── models/                   # 数据模型
│   ├── services/                 # 业务逻辑
│   ├── routes/                   # API 路由
│   └── scripts/                  # 数据工具脚本
│       ├── generate_seed_data.py # 数据生成脚本
│       ├── validate_data.py      # 数据校验脚本
│       ├── check_frontend_files.py # 前端文件检查
│       └── e2e_smoke_check.py    # E2E smoke 检查
├── frontend/                     # 前端代码
│   ├── index.html                # 首页
│   ├── recommendation.html       # 旅游推荐
│   ├── route_planning.html       # 路线规划
│   ├── nearby.html               # 场所查询
│   ├── indoor_navigation.html    # 室内导航 Demo
│   ├── css/style.css             # 统一样式
│   └── js/
│       ├── api.js                # API 调用封装
│       ├── map.js                # Leaflet 地图交互
│       ├── index.js              # 首页统计加载
│       ├── recommendation.js     # 推荐页面交互
│       ├── route_planning.js     # 路线规划交互
│       ├── nearby.js             # 场所查询交互
│       └── indoor_navigation.js  # 室内导航交互
├── data/                         # JSON 数据文件
│   ├── destinations.json         # 200+ 目的地
│   ├── internal_maps.json        # 内部地图模板
│   ├── internal_nodes.json       # 内部节点
│   ├── internal_edges.json       # 内部道路边
│   ├── facilities.json           # 服务设施
│   ├── users.json                # 用户数据
│   └── indoor_graphs.json        # 室内导航图（可选）
└── tests/                        # 测试
    ├── conftest.py
    ├── test_algorithms/
    ├── test_models/
    ├── test_services/
    └── test_routes/
```

## 数据规模（当前状态）

| 数据项 | 要求 | 实际 |
|--------|------|------|
| 目的地 | >= 200 | **217** (30 校园 + 187 景区) |
| 内部地图模板 | >= 3 | **5** (2 真实 + 3 抽象) |
| 内部节点总数 | >= 90 | **164** |
| 每地图实体节点 | >= 20 | **22** (抽象模板) / **14, 13** (真实模板) |
| 道路边 | >= 200 | **416** |
| 服务设施 | >= 50 | **88** |
| 设施类别 | >= 10 | **15** |
| 用户 | >= 10 | **12** |
| 室内建筑 | >= 1 | **1** |

### 核心设计说明

- **200+ 目的地通过 internal_map_id 复用 3 套内部地图**，避免为每个目的地单独制作地图
- 路线规划和场所查询**只在同一个 internal_map_id 内部进行**
- 不做城市级外部导航，不做跨景区路线规划

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成数据
python backend/scripts/generate_seed_data.py

# 3. 校验数据
python backend/scripts/validate_data.py

# 4. 运行全部测试
pytest tests/ -q

# 5. 检查前端文件
python backend/scripts/check_frontend_files.py

# 6. 启动后端（终端 1）
cd backend
python app.py

# 7. E2E smoke 检查（终端 2，需后端已启动）
python backend/scripts/e2e_smoke_check.py

# 8. 启动前端（终端 3）
cd frontend
python -m http.server 8080

# 9. 浏览器访问前端页面
http://127.0.0.1:8080
```

> 后端默认端口 5000，前端默认端口 8000。后端已启用 CORS。
> 请确保后端和前端同时运行，前端页面依赖后端 API。

### 页面地址

| 页面 | 地址 |
|------|------|
| 首页 | http://127.0.0.1:8080 |
| 旅游推荐 | http://127.0.0.1:8080/recommendation.html |
| 路线规划 | http://127.0.0.1:8080/route_planning.html |
| 场所查询 | http://127.0.0.1:8080/nearby.html |
| 室内导航 Demo | http://127.0.0.1:8080/indoor_navigation.html |

## 测试命令

```bash
# 地图坐标诊断
python backend/scripts/diagnose_map_coordinates.py

# 数据校验（384,969 checks）
python backend/scripts/validate_data.py

# 算法测试（113 tests）
pytest tests/test_algorithms -q

# 服务层测试（55 tests）
pytest tests/test_services -q

# API 路由测试（39 tests）
pytest tests/test_routes -q

# 全部测试（207 tests）
pytest tests/ -q

# 前端文件检查
python backend/scripts/check_frontend_files.py

# E2E smoke 检查（需先启动后端）
python backend/scripts/e2e_smoke_check.py
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [系统设计](docs/system_design.md) | 架构概览、分层职责、数据流 |
| [数据结构设计](docs/data_structure_design.md) | JSON schema 定义 |
| [算法设计](docs/algorithm_design.md) | 核心算法说明 |
| [API 设计](docs/api_design.md) | API 端点文档 |
| [地图数据策略](docs/map_data_strategy.md) | 真实地图 vs 抽象模板策略 |
| [前端使用指南](docs/frontend_usage.md) | 页面操作步骤、常见问题 |
| [答辩演示脚本](docs/demo_script.md) | 验收讲解流程、常见追问 |
| [端到端验收报告](docs/e2e_acceptance_report.md) | 页面验收记录、约束确认 |
| [测试报告](docs/test_report.md) | 测试范围、结果、覆盖统计 |
| [阶段完成报告](docs/phase1_completion_report.md) | Phase 1 实现总结 |
| [未来扩展](docs/future_extensions.md) | Phase 2 扩展备忘 |

## 开发阶段

- [x] 第 0 步：项目设计、目录规划、文档骨架
- [x] 第 1 步：生成符合课程要求的数据集 + 数据校验脚本
- [x] 第 2 步：实现核心算法（Graph、Dijkstra、Top-K、排序、查找、附近查询）+ 算法单元测试（113 tests）
- [x] 第 3 步：实现后端服务和路由 + 服务/路由测试（94 tests） — Total: 207 passed
- [x] 第 4 步：实现前端页面（5 个 HTML + 7 个 JS + 1 个 CSS + Leaflet 地图）
- [x] 第 5 步：端到端验收、smoke 检查、测试报告、阶段完成报告、答辩演示脚本
- [x] 地图真实性修正：新增 MAP_BUPT_REAL + MAP_SCENIC_REAL，前端 show_tile 逻辑，新增 API
- [x] 地图展示与坐标修复：修复 BUPT 坐标偏移、抽象模板 (0,0) 坐标、前端分层管理（baseLayer/routeLayer/markerLayer）、完整内部路网绘制、新增 map-layers API、新增坐标诊断脚本
- [x] 附近查询优化：单源 Dijkstra (O(F×V²) → O(V²+F log F))，多目标复选框交互替换文本输入，测试 207 passed

## 课程信息

- 课程：数据结构课程设计
- 项目：基于智能体的个性化旅游系统
- 要求：核心算法自行实现，JSON 存储，不使用数据库
