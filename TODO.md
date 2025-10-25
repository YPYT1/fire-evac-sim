# TODO 计划

## 阶段 0：环境与基础设施准备
- [x] 确认开发环境：Python 3.11、uv、Bun ≥1.2.23、Node 生态依赖、Three.js 工具链。（详见 `docs/ENVIRONMENT.md`。）
- [x] 初始化 Git 仓库分支策略与提交规范（约定 Conventional Commits + 中文/英文注释策略）。详见 `docs/GIT_WORKFLOW.md`。
- [x] 创建 `backend/` 与 `frontend/` 目录结构，占位 `README`，并配置 `.gitignore`、`.editorconfig`、`.pre-commit-config.yaml`。
- [x] 使用 `uv` 初始化 Python 项目，锁定依赖（fastapi、uvicorn、numpy、pydantic、pyyaml，`python-rvo2` 将在编译验证后补充）。详见 `docs/DEPENDENCIES.md`。
- [x] 初始化 Bun + Vite + Vue 3 + TypeScript 项目，安装 three、pinia、vue-router、@types/three 等依赖。（见 `frontend/` 项目与 `bun.lockb`。）
- [x] 配置统一的 lint & format：Python (ruff/black) 与 TypeScript (eslint/prettier)，并集成 pre-commit 钩子。（参见 `.pre-commit-config.yaml`、`backend/pyproject.toml`、`frontend/.eslintrc.cjs`、`.prettierrc.json`。）

## 阶段 1：后端仿真内核与 API
### 1.1 核心目录
- [x] 建立 `backend/app/` 包结构：`main.py`、`api/`, `services/`, `core/`（骨架已创建，待补全业务逻辑）。
- [x] 创建 `backend/app/core/config.py` 读取 `simulation.yaml` / 环境变量（提供基础 Settings + YAML 加载）。
- [x] 设计 pydantic 模型：模拟参数、代理状态、火源数据、入口/出口定义（`core/schemas.py` 占位实现）。

### 1.2 地图与网格
- [x] 实现 `backend/app/sim/grid.py`，解析 `demo_map.json`，构建网格、可行走区域、出口标记（占位栅格实现）。
- [x] 提供网格到世界坐标转换工具，便于前端 (x, y) ↔ (x, z)（`sim/utils.py`）。

### 1.3 规划与避障
- [x] 实现 `backend/app/sim/planner.py`：A* 路径规划（初版占位）。
- [x] 实现 `backend/app/sim/fire.py`：火源代价场占位算法。
- [x] 封装 `backend/app/sim/rvo.py`：RVO2 占位封装，支持无依赖 fallback。
- [x] 设计可切换避障策略（RVO2 / rvo2-py / 社会力模型 fallback）。已支持配置选择与缺失包回退 simple。

### 1.4 会话管理与调度
- [x] 开发 `backend/app/services/session_manager.py` 管理会话生命周期（占位实现，仅记录状态）。
- [x] 实现模拟主循环（异步）：tick 更新、重规划触发、火源动态刷新（SessionManager 启动背景任务，支持 fires 更新）。
- [x] 支持手动模式下的火点插入与重算（/sim/replan 现会更新 state.fires 并记录重规划请求）。

### 1.5 API 层
- [x] FastAPI 启动文件 `main.py`：加载配置、注册路由、日志（CORS/异常待完善）。
- [x] REST 接口：`POST /sim/start`、`POST /sim/replan`、`GET /sim/status`、`POST /sim/stop`（返回占位数据）。
- [x] WebSocket：`/ws/sim/{session_id}`，推送占位数据流。
- [x] 编写依赖注入（Depends）与后台任务，确保线程安全与资源释放（`dependencies.get_session_manager` + BackgroundTasks）。

### 1.6 后端测试与验证
- [x] 使用 pytest 编写单元测试：网格加载、火场代价、A* 正确性、RVO2 步进（见 `backend/tests/`）。
- [x] 添加集成测试：模拟会话从 start→status→stop 全链路（见 `tests/test_simulation_flow.py`）。
- [x] 配置 GitHub Actions / 本地 CI 任务运行测试与静态检查（见 `.github/workflows/ci.yml`）。

## 阶段 2：前端三维可视化与交互
### 2.1 项目结构
- [x] 组织 `frontend/src/`：`main.ts`, `App.vue`, `router`, `store`, `components`, `three`。
- [x] 创建基础路由与布局，预留控制面板与画布区域（`router.ts` + `SimulationView.vue`）。
- [x] 明确自建建筑与房间模型方案，已创建 `three/models/House.ts` 占位并在文档强调自建模型。

### 2.2 Three.js 场景
- [x] 编写 `three/scene.ts` 设置渲染器、相机、光照、网格地面。
- [x] 实现 `three/models/House.ts` 占位并集成到 SceneCanvas。
- [x] 使用 InstancedMesh 渲染人群；封装 `three/agents.ts` 管理代理实例更新。
- [x] 构建火源可视化：`three/fire.ts` Sprite 占位。

### 2.3 状态管理与通信
- [x] 配置 Pinia store：保存会话状态、代理列表、火源（`store/simStore.ts`）。
- [x] 封装 API 客户端：REST + WebSocket（`api/client.ts`，重连/心跳待完善）。
- [x] 设计数据解构：从 WebSocket 帧中提取 agents/fires，更新 Three.js 实例（SceneCanvas 监听 store）。

### 2.4 UI 与交互
- [x] `ControlPanel.vue`：模式切换、参数输入、启动/停止按钮。
- [x] `FirePanel.vue`：火点列表展示，随机生成 & 手动拾取待实现。
- [x] 实现 manual 模式下的鼠标拾取，触发后端 `replan`（SceneCanvas + simStore）。
- [x] 添加状态面板：总人数、平均速度、瓶颈提示（StatusPanel 实时展示 stats）。

### 2.5 前端测试与优化
- [x] 配置 Vitest/Testing Library，针对 store 与组件的单元测试（`vitest.config.ts` + `simStore.spec.ts`）。
- [x] 视图层 e2e（Playwright）验证启动后渲染与 WebSocket 数据同步（`playwright.config.ts` + `tests/e2e/basic.spec.ts`）。
- [x] 性能优化：调优渲染循环、节流 WS 更新、清理资源（WebSocket tick 节流 + store cleanup）。

## 阶段 3：联调与验证
- [x] 编写联调脚本：启动后端、前端并模拟多场景（见 `scripts/integration_runner.py` + `docs/INTEGRATION.md`）。
- [x] 对齐坐标系，验证后端网格数据与前端模型一致性（联调脚本自动校验 `building_alignment.json`）。
- [x] 针对极端场景（超大人群、出口阻塞）观察性能与稳定性，记录瓶颈（`scripts/stress_probe.py` + `docs/STRESS_TEST.md`）。
- [x] 将核心参数（tick_hz、速度分布、火源扩散系数）抽到配置文件并验证热更新策略（新增配置项 + `test_config_hot_reload.py`）。

## 阶段 4：部署与文档
- [x] 更新根目录 README：运行步骤、配置说明、扩展路线。
- [x] 输出用户使用手册：如何创建场景、如何手动添加火点、常见问题（见 `docs/USER_GUIDE.md`）。
- [x] 编写一键启动脚本：macOS 与 Ubuntu 两份（`start_macos.sh` / `start_ubuntu.sh`，包含实时日志输出）。
比如我直接运行这个一键启动的脚本，他就会正常启动前端和后端，并且还有日志直接输出
