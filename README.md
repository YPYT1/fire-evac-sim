# fire-evac-sim
# README
# README

# 🔥 Fire Evacuation Simulation Platform
### —— 基于 Python 3.11 + FastAPI + RVO2 + Vue 3 + Three.js + Bun 的建筑火灾疏散仿真系统

# 🧭 一、项目简介（Project Overview）
**Fire-Evac-Sim** 是一个基于浏览器的三维可视化火灾疏散仿真平台。 项目旨在通过 **数字孪生建筑模型** + **智能疏散算法**，重现火灾场景中人员的实时避障与逃生过程。
系统采用：
* **前端三维可视化**（Three.js + Vue 3 + Bun）展示建筑、火源、烟雾与人员运动；
* **后端物理与行为仿真**（Python 3.11 + FastAPI + RVO2）进行路径规划、避障决策与动态重算；
* **统一通信机制**（WebSocket + REST API）在前后端间同步状态。

⠀本项目既是一个科研实验平台，也可作为教学演示与应急预案可视化的基础框架。

---

# 🛠️ 技术栈版本说明（Technology Stack）

## 后端技术栈（Backend）

| 技术 | 版本 | 用途 | 兼容性状态 |
|------|------|------|-----------|
| **Python** | **3.11** | 核心运行环境 | ✅ 推荐版本（稳定） |
| **uv** | 0.8.11+ | Python 包管理器 | ✅ 已验证 |
| **FastAPI** | 0.120.0+ | REST API + WebSocket 服务 | ✅ 完全支持 Python 3.8-3.14 |
| **uvicorn** | 最新 | ASGI 服务器 | ✅ 完全兼容 |
| **NumPy** | 2.x | 数值计算与矩阵运算 | ✅ 完全支持 Python 3.11 |
| **NetworkX** | 3.x | 图算法（路径规划可选） | ✅ 完全兼容 |
| **Pydantic** | 2.x | 数据验证与序列化 | ✅ 完全支持 |
| **PyYAML** | 6.x | 配置文件解析 | ✅ 完全兼容 |
| **Python-RVO2** | 最新 | 多智能体避障算法 | ⚠️ 需要编译（见备选方案） |

### RVO2 避障方案说明

**优先方案**：Python-RVO2（需要 C++ 编译环境）
- 性能最优，适合大规模仿真（1000+ 代理）
- 需要系统依赖：
  - macOS: `xcode-select --install`
  - Ubuntu/Debian: `build-essential cmake`
  - Windows: Visual Studio Build Tools (C++)

**备选方案**（如果 RVO2 编译失败）：
1. **rvo2-py**：纯 Python 实现，无需编译，性能稍差但稳定
2. **社会力模型（Social Force Model）**：更简单的避障算法
3. **前端实现**：使用 TypeScript + ORCA.js 在前端实现避障

---

## 前端技术栈（Frontend）

| 技术 | 版本 | 用途 | 兼容性状态 |
|------|------|------|-----------|
| **Bun** | **1.2.23+** | JavaScript 运行时 + 包管理器 | ✅ 已安装验证 |
| **Vue** | **3.5.x** | 渐进式 JavaScript 框架 | ✅ 完全兼容 Bun |
| **TypeScript** | **5.x** | 类型安全的 JavaScript 超集 | ✅ Bun 原生支持 |
| **Vite** | **6.x** | 下一代前端构建工具 | ✅ 完全兼容 Bun |
| **Three.js** | **0.170.x** | 3D 图形渲染引擎 | ✅ 完全兼容 |
| **Pinia** | **2.x** | Vue 状态管理库 | ✅ Vue 3 官方推荐 |
| **Vue Router** | **4.x** | Vue 官方路由管理器 | ✅ Vue 3 专用版本 |
| **@types/three** | 最新 | Three.js TypeScript 类型定义 | ✅ 完全支持 |

### 为什么选择 Bun？

- **性能优势**：启动速度比 Node.js 快 4 倍，包管理比 npm 快 30 倍
- **原生 TypeScript**：无需额外配置即可运行 `.ts` 文件
- **Web 标准 API**：内置 `fetch`、`WebSocket` 等现代 API
- **完全兼容**：可运行所有 Node.js 生态的包（Vue、Three.js 等）

---

## 开发工具与环境

| 工具 | 版本要求 | 说明 |
|------|---------|------|
| **操作系统** | macOS / Linux / Windows | 已在 macOS (Darwin 24.6.0) 测试 |
| **Git** | 2.x+ | 版本控制 |
| **CMake** | 3.x+ | RVO2 编译依赖（可选） |
| **Xcode Command Line Tools** | 最新 | macOS 编译环境（可选） |

---

## 版本选择说明

### Python 版本：为什么选择 3.11？

1. **稳定性**：Python 3.11 是成熟稳定的版本，生态支持完善
2. **性能**：相比 3.10 提升 10-60% 的性能
3. **兼容性**：所有依赖库（FastAPI、NumPy 等）完全支持
4. **RVO2 兼容性**：虽然官方只测试到 3.6，但 3.11 编译成功率更高

### 前端包管理器：为什么选择 Bun？

1. **速度**：安装依赖速度是 npm 的 30 倍，pnpm 的 2 倍
2. **简化工作流**：一个工具替代 Node.js + npm + tsx
3. **现代化**：原生支持 TypeScript、JSX、ESM
4. **兼容性**：100% 兼容 npm 生态，可无缝迁移

---

## 系统要求

### 最低配置
- CPU: 双核 2.0 GHz
- 内存: 4 GB RAM
- 存储: 2 GB 可用空间
- 浏览器: Chrome 90+ / Firefox 88+ / Safari 14+

### 推荐配置
- CPU: 四核 3.0 GHz+
- 内存: 8 GB RAM+
- 存储: 5 GB 可用空间
- 显卡: 支持 WebGL 2.0
- 浏览器: Chrome 最新版 / Edge 最新版

---

# 🚀 本地快速开始（Local Quickstart）

> 本项目默认在本机运行，无需部署远程环境。以下步骤在 macOS 与 Ubuntu 上已经验证。

## 1. 环境准备
- 安装 [uv](https://docs.astral.sh/uv/) 并确保满足 Python 3.11 环境。
- 安装 [Bun](https://bun.sh/) ≥ 1.2.23。
- （可选）若需编译 `python-rvo2`，请提前安装系统编译工具（macOS: `xcode-select --install`，Ubuntu: `sudo apt install build-essential cmake`）。

## 2. 同步依赖
```bash
# 后端依赖
uv sync

# 前端依赖
cd frontend
bun install
```

## 3. 启动服务
1. 手动启动：
   ```bash
   # 终端 A - 后端
   uv run uvicorn backend.app.main:app --reload

   # 终端 B - 前端
   cd frontend
   bun dev --host
   ```
   默认后端监听 `http://127.0.0.1:8000`，前端 `http://127.0.0.1:5173`。

2. 一键脚本（推荐）：
   - macOS: `./start_macos.sh`
   - Ubuntu: `./start_ubuntu.sh`

   脚本会自动检测/安装缺失的 Python、uv、Bun、Node.js 及 RVO2 避障库（先从 `third_party/python-rvo2` 本地源码安装，失败再尝试联网；首次运行可能提示输入管理员密码），并在根目录创建 `logs/` 文件夹实时输出前后端日志。

3. 停止服务：按 `Ctrl+C` 或终止脚本即可，日志保留在 `logs/backend.log` 与 `logs/frontend.log`。

## 4. 验证运行
- 访问前端页面，点击「启动仿真」查看 Three.js 场景与实时状态面板。
- 若需联调测试，可执行 `python scripts/integration_runner.py`。
- 极端场景压力测试：`python scripts/stress_probe.py`。

---

# 🧩 配置要点（Configuration Highlights）

| 文件 | 作用 | 关键字段 |
|------|------|----------|
| `backend/app/data/config/simulation.yaml` | 仿真主配置 | `sim.tick_hz`、`agents.speed.mean/std`、`fire.diffusion_decay`、`map.file` |
| `backend/app/data/maps/demo_map.json` | 占据栅格 | `width`、`height`、`cellSize`、`exits` |
| `frontend/public/models/building_alignment.json` | 前后端坐标对齐 | `grid.*`、`model.offset/scale/rotation_y_deg`、`anchors` |
| `.env.example` | 前后端共享的环境变量模板 | `VITE_BACKEND_URL` 等 |

> 修改配置后可直接重启后端；`load_simulation_config` 支持热加载校验，详见 `backend/tests/test_config_hot_reload.py`。

---

# 🛠️ 扩展路线（Extension Roadmap）

1. **算法增强**：引入更高阶的群体行为模型（Social Force、APSO-FD），并补充对应测试。
2. **多楼层/多出口**：扩展 `demo_map.json` 结构，搭配 `building_alignment.json` 对齐多层模型。
3. **联调自动化**：在 `scripts/stress_probe.py` 基础上扩展更多场景，并接入 CI 统计。
4. **部署脚本**：可在现有一键启动脚本上添加 Docker / systemd 模式，支持远程部署。
5. **用户手册升级**：结合真实建筑 glTF 模型，形成针对不同角色（建模、运维、演示）的多份指南。

---

# 🎯 二、项目目标与意义（Objectives & Significance）
### 1. 研究目标
* 构建一个**可交互的建筑火灾疏散仿真环境**；
* 通过**算法与三维可视化结合**，实现个体-群体层面的疏散行为再现；
* 为论文研究（如 APSO-FD 优化算法）提供可验证的运行环境；
* 验证不同疏散策略、出口配置、火源布置对总体疏散效率的影响。

⠀2. 实际意义
* 可辅助**消防规划、建筑设计与安全评估**；
* 用于高校课程中的**智能仿真教学与研究实验**；
* 为后续接入 **数字孪生城市平台** 提供可扩展基础；
* 在紧急预案演练或应急管理平台中提供可视化支持。

⠀
# ⚙️ 三、系统功能与模块设计（System Functions）
| **模块** | **功能说明** | **技术实现** |
|:-:|:-:|:-:|
| 🔸 **建筑模型展示** | 渲染 3D 建筑内部结构（楼层、房间、出口） | Three.js + 自定义房屋模型（或 glTF 导入） |
| 🔸 **火源与烟雾可视化** | 固定、随机、交互三种模式生成火点；烟雾以粒子或体渲染形式扩散 | Three.js 粒子系统 / shader |
| 🔸 **路径规划算法** | 基于 A* / Dijkstra / APSO-FD 生成最优疏散路径 | Python + Numpy + NetworkX |
| 🔸 **避障与群体行为** | 使用 RVO2 实现多智能体无碰撞运动与局部决策 | RVO2 (Python binding) |
| 🔸 **实时仿真与通信** | 后端按 tick 更新位姿并通过 WebSocket 推送前端 | FastAPI + WebSocket |
| 🔸 **三维动态渲染** | 人员移动、路径轨迹、火势变化实时可视化 | Vue + Three.js 动画循环 |
| 🔸 **参数控制与模式切换** | 可视化面板调整人数、速度、出口、火点模式 | Vue 控制面板（Pinia 状态） |
| 🔸 **统计与输出** | 输出平均疏散时间、瓶颈点、路径热力图 | Python 分析模块 + 前端数据面板 |

# 🔬 四、研究/开发思路（Design Logic）
**1** **数据层**
	* 使用简化的建筑平面图（JSON 栅格或 NavMesh）作为行走区域；
	* 通过 YAML 配置定义火点模式、人员数量、速度分布；
	* 代价场（Cost Field）在后端生成并动态调整。
**2** **算法层**
	* 全局路径：A* / APSO / PSO 负责从起点到出口的最优规划；
	* 局部运动：RVO2 保证代理间不碰撞；
	* 火点动态：火源温度或烟雾浓度影响局部代价权重；
	* 可选接入 FDS（Fire Dynamics Simulator）输出，构建真实热场。
**3** **通信层**
	* REST API 用于启动/停止/重规划；
	* WebSocket 实时推送每帧代理状态 {id, pos, vel}；
	* 前端订阅数据流更新 Three.js 场景。
**4** **可视化层**
	* Three.js 渲染建筑与移动对象；
	* Vue 管理 UI、参数输入与状态；
	* 实现动态视角、速度调节、路径线显示开关。

⠀
# 🧩 五、系统运行效果目标（Expected Outcomes）
系统运行时应具备以下可观测效果：
**1** **三维建筑场景**
	* 可显示楼层、房间、通道、出口；
	* 用户可旋转/缩放/平移视角。
**2** **火灾点与烟雾扩散**
	* 支持固定、随机或点击生成火点；
	* 火源处出现粒子/红光，烟雾呈半透明体；
	* 火源周围区域在地图上代价提高。
**3** **人群疏散动画**
	* 数百名代理从起点（如大厅）同时向出口移动；
	* 个体之间不相撞（RVO2 避障）；
	* 遇火点时自动绕行；
	* 出口被堵时会重新规划路径。
**4** **实时交互与监控**
	* 控制面板可切换火点模式、人数、速度；
	* 可暂停/恢复仿真；
	* 显示疏散进度、剩余人数、平均速度。
**5** **结果分析**
	* 自动计算总疏散时间、瓶颈区域；
	* 支持导出统计表与轨迹数据；
	* 可生成热力图或路径动画回放。

⠀
# 🧱 六、系统结构图（概要）
### ┌─────────────────────────────┐
### │         Frontend (Vue + Three.js)       │
### │ ┌───────────────────────────────────┐ │
### │ │ 建筑模型 | 火源 | 烟雾 | 人群动画 | 控制面板 │ │
### │ └───────────────┬───────────────────┘ │
### │                 │ WebSocket / REST       │
### └─────────────────┼───────────────────────┘
###                   │
### ┌─────────────────▼───────────────────────┐
### │          Backend (FastAPI + RVO2)       │
### │ ├─ config.yaml  → 模拟参数              │
### │ ├─ grid.py      → 地图与代价场          │
### │ ├─ planner.py   → A* / APSO 路径规划    │
### │ ├─ rvo.py       → 多智能体避障          │
### │ ├─ fire.py      → 火点代价动态更新      │
### │ └─ state.py     → 仿真循环与帧同步      │
### └────────────────────────────────────────┘

# 📊 七、性能与测试指标（Evaluation Metrics）
| **指标** | **描述** | **目标** |
|:-:|:-:|:-:|
| **仿真稳定性** | 仿真运行 1000 代理不掉帧 | ≥ 20 FPS |
| **路径最优性** | 平均路径长度与理论最短比 | ≤ 1.1 |
| **避障安全率** | 无碰撞或穿模事件比例 | 100% |
| **实时交互延迟** | 后端推送→前端渲染的平均延迟 | ≤ 100 ms |
| **多火点适应性** | 多火源时可重新规划路径 | 支持动态更新 |

# 🔄 八、预期成果与应用（Expected Deliverables）
1 ✅ **运行平台** 一个完整可运行的前后端项目，可在浏览器中实时显示疏散过程。
2 ✅ **算法模块** 可独立复用的路径规划与避障引擎（A* + RVO2 + Fire Cost Field）。
3 ✅ **交互演示** 用户可手动设定火点、人数与出口，并即时查看疏散效果。
4 ✅ **科研支撑** 可嵌入论文或项目报告，展示改进算法（如 APSO-FD）在不同场景下的性能差异。
5 ✅ **扩展基础** 可接入烟气传播（FDS）、多楼层建筑、传感器数据或 IoT 数字孪生接口。


⠀
#
## 1) 火灾点的定义（建议支持三种模式）
为“整体能跑通、代码量少”并便于后续扩展，后端统一从配置或参数里切换模式：
* **默认：fixed（固定火点）**
  * 可复现性最好，做论文/演示稳定。
  * 配置：config/simulation.yaml 里写 fire.mode: fixed 与 fire.fixed_points: [[x,y,z], ...]。
* **随机：random**
  * 快速做压力/鲁棒性测试。
  * 配置：fire.mode: random（可加 fire.random.count、seed）。
* **交互：manual（前端点选）**
  * 前端在 Three.js 场景里点选地面/楼层，把坐标 POST 给 /sim/start。
  * 方便做演示或临时场景。

⠀路径规划时，后端会把火点映射为**危险代价场（hazard/cost field）**，动态提高这些栅格或边的权重，A* 更偏向绕开；RVO2 负责个体之间的避碰与微调。

## 2) 前端“写模型”的代码放哪
前端用 **Vue + Vite + TypeScript + Three.js**，把三维相关集中到 src/three 下，Vue 组件只做容器/UI：
* src/three/scene.ts：Three.js 场景创建、灯光、相机、渲染循环。
* src/three/loaders.ts：加载 glTF 建筑模型（如 public/models/building.glb）。
* src/three/agents.ts：人群渲染（建议 InstancedMesh 提升性能）。
* src/three/fire.ts：火点显示（精简可用 Sprite/粒子；后续可改 Shader）。
* src/three/paths.ts：后端返回的路径折线 → Line/TubeGeometry 可视化。
* src/components/SceneCanvas.vue：一个 Vue 组件挂载 Three 场景、处理 WebSocket/事件。
* src/api/client.ts：封装与 FastAPI 的 REST/WebSocket 通信。

⠀这样你在 **src/three/*** 专心写 3D 逻辑，在 **SceneCanvas.vue** 里拼装、订阅后端推送即可。

## 3) 整体项目框架（树形目录）
下面是一个**单仓库**、前后端分目录，直接可用 uv 管理 Python 依赖、vite 管理前端的结构。你可以一键粘贴给 Claude Code 生成骨架文件。
fire-evac-sim/
├─ README.md
├─ .env.example
├─ .gitignore
├─ pyproject.toml                 # 使用 uv 管理：fastapi、uvicorn、rvo2、numpy 等
├─ uv.lock                        # 由 uv 自动生成
├─ backend/
│  ├─ app/
│  │  ├─ main.py                  # FastAPI 入口（含 REST + WebSocket）
│  │  ├─ api/
│  │  │  ├─ routes_sim.py         # /sim/start /sim/stop /sim/status 等
│  │  │  └─ ws.py                 # /ws/sim/{session_id} 推送代理位置/路径
│  │  ├─ core/
│  │  │  ├─ config.py             # 读取 config/simulation.yaml、环境变量
│  │  │  └─ schemas.py            # Pydantic 请求/响应模型（场景、火点、代理参数）
│  │  ├─ sim/                     # —— 核心模拟逻辑（尽量精简）
│  │  │  ├─ state.py              # 仿真全局状态（agents、goals、地图、火点）
│  │  │  ├─ grid.py               # 简单占据栅格/代价场（从楼层平面或JSON加载）
│  │  │  ├─ fire.py               # fire.mode: fixed/random/manual；生成危险代价场
│  │  │  ├─ planner.py            # A* / Dijkstra（首版就 A*），输出路径点列
│  │  │  ├─ rvo.py                # RVO2 封装：根据目标速度做局部避碰更新
│  │  │  └─ utils.py              # 坐标换算/插值/采样等
│  │  ├─ data/
│  │  │  ├─ maps/
│  │  │  │  └─ demo_map.json      # 栅格/节点图（与前端 glTF 对齐的平面投影）
│  │  │  ├─ models/
│  │  │  │  └─ building.glb       # 可选：后端也放一份（通常前端加载 public 的）
│  │  │  └─ config/
│  │  │     └─ simulation.yaml    # fire 模式、agent 数量、速度、刷新率等
│  │  └─ services/
│  │     └─ session_manager.py    # 多会话/多场景管理（可选，后续扩展）
│  ├─ tests/
│  │  ├─ test_planner.py
│  │  └─ test_rvo.py
│  └─ scripts/
│     ├─ run_dev.sh               # uv run uvicorn backend.app.main:app --reload
│     └─ seed_map.py              # 把平面图转栅格的简单脚本（可选）
│
└─ frontend/
   ├─ package.json
   ├─ vite.config.ts
   ├─ tsconfig.json
   ├─ .env.development
   ├─ public/
   │  └─ models/
   │     └─ building.glb          # 前端直接加载，运维时可上 CDN
   └─ src/
      ├─ main.ts                  # 创建 app，注册 router/store
      ├─ App.vue
      ├─ router.ts
      ├─ api/
      │  └─ client.ts             # REST + WebSocket 封装
      ├─ store/
      │  └─ simStore.ts           # Pinia：会话ID、模式、UI 状态
      ├─ components/
      │  ├─ SceneCanvas.vue       # Three 场景、渲染循环、事件绑定
      │  ├─ ControlPanel.vue      # 开始/停止、人数、模式（fixed/random/manual）
      │  └─ FirePanel.vue         # 火点列表、随机参数、权重调节
      └─ three/
         ├─ scene.ts              # 场景/相机/灯光/renderer 初始化
         ├─ loaders.ts            # glTF/纹理加载
         ├─ agents.ts             # InstancedMesh 管理（增删/更新矩阵）
         ├─ fire.ts               # 火点可视化（Sprite/粒子，后续可 Shader）
         └─ paths.ts              # 路径线段可视化（Line/TubeGeometry）

## 运行与依赖（一句话版）
**后端（uv + uvicorn）**
uv add fastapi uvicorn rvo2 numpy pydantic pyyaml
uv run uvicorn backend.app.main:app --reload
**前端（Bun + Vite）**
bun create vite frontend --template vue-ts
cd frontend && bun install three pinia vue-router @types/three
bun run dev

## 数据流（超简流程）
1 前端载入 building.glb → 选择模式（fixed/random/manual）→ 设定人数/出口。
2 POST /sim/start（携带模式与参数）→ 后端：构造代价场 → A* 生成每个代理的全局路径 → 建立 RVO2 仿真器。
3 前端连 WS /ws/sim/{id} → 实时接收 {positions, paths(optional), fires} → Three.js 动画。
4 必要时 POST /sim/replan（火情/堵塞变化）→ 后端重算路径并热更新。

⠀
## 环境准备
* **Python**：3.11（推荐使用 [uv](https://github.com/astral-sh/uv) 作为包与运行器）。
* **Bun**：1.2.23+（替代 Node.js + npm，更快的 JavaScript 运行时）。
* **系统依赖（RVO2 构建可能需要）**：
  * macOS：xcode-select --install
  * Ubuntu/Debian：build-essential cmake
  * Windows：安装 Visual Studio Build Tools（C++），再用 uv 构建
* 如果 rvo2 针对 Python 3.13 的预编译轮子不可用，将触发本地编译。若编译困难，可临时使用**纯 TS 方案**（前端用 pathfinding.js 做寻路，避障先简单规则），或使用 Python 3.11（推荐版本）。

⠀
## 配置文件（backend/app/data/config/simulation.yaml）
最小字段建议：

```yaml
sim:
  mode: fixed             # fixed | random | manual
  tick_hz: 20             # 仿真步频（10~30 推荐）
  avoidance_strategy: rvo2
  seed: 42

fire:
  mode: fixed
  diffusion_decay: 0.92   # 火焰邻域每格的衰减系数
  fixed_points:
    - position: [2.0, 0.0, 3.0]
      intensity: 1.0
    - position: [7.5, 0.0, 6.0]
      intensity: 0.8
  random:
    count: 2
    radius: 4.0
    intensity_range: [0.6, 1.2]

map:
  file: backend/app/data/maps/demo_map.json
  cell_size: 1.0
  origin: [0.0, 0.0, 0.0]

agents:
  count: 200
  speed:
    mean: 1.3             # m/s
    std: 0.2
  start_region:
    - id: lobby
      rect: [1, 1, 4, 3]
  goal_regions: ["exitA", "exitB"]

costs:
  base: 1.0
  fire_weight: 3.0
  congestion_weight: 1.2
  distance_weight: 1.0
  exit_bonus: 0.5
```

## 地图与数据文件（demo_map.json）
用于后端 A* 的简化占据栅格或节点图（与前端 glTF 的平面对齐）。建议结构（示例）：
{
  "type": "grid",
  "cellSize": 0.5,
  "width": 80,
  "height": 60,
  "walkable": "010101... (可为二维数组或RLE)",
  "regions": {
    "hall":   { "rect": [0,0,20,10] },
    "exitA":  { "rect": [78,5,2,2] },
    "exitB":  { "rect": [1,55,2,2] }
  }
}
坐标系约定：后端二维网格使用 (x, y)，前端 Three.js 显示时映射到 (x, z)，高度用 y。cellSize 决定像素到米的映射。

## 接口协议（REST + WebSocket）
### REST
* POST /sim/start **请求体（示例）**： {
* "mode": "fixed",            // fixed | random | manual
* "fires": [[2.0,0.0,3.0]],   // manual 时必填
* "agents": { "count": 200, "speedMean": 1.3, "speedStd": 0.2 },
* "goals": ["exitA","exitB"]
* }
*  **响应**： { "session_id": "abc123", "tick_hz": 20 }
*
* POST /sim/replan **请求体**： { "session_id": "abc123", "fires": [[4.5,0.0,6.0]], "reason": "new_hazard" }
*  **响应**：{ "ok": true }
* GET /sim/status?session_id=abc123 → 返回运行状态（人数、平均速度、阻塞率、tick 配置、火焰扩散系数等）。
* POST /sim/stop → 结束会话，释放资源。

⠀WebSocket
* GET /ws/sim/{session_id} **服务端推送帧（示例）**： {
*   "type": "state",
*   "tick": 120,
*   "tick_hz": 20,
*   "agents": [
*     { "id": 1, "position": [1.2,0.0,3.4], "velocity": [0.8,0.0,0.1] },
*     { "id": 2, "position": [1.0,0.0,3.1], "velocity": [0.7,0.0,0.2] }
*   ],
*   "fires": [
*     { "position": [2.0, 0.0, 3.0], "intensity": 1.0 }
*   ],
*   "stats": {
*     "agent_count": 180,
*     "active_agents": 172,
*     "average_speed": 1.25,
*     "congestion_ratio": 0.86,
*     "speed_mean": 1.3,
*     "speed_std": 0.2,
*     "fire_decay": 0.92
*   }
* }
*  其他类型：hello、end、error。

⠀
## 前端开发约定
* **模型**：手写 3D 房子模型请放到 frontend/src/three/models/（例如 House.ts），导出工厂函数返回 THREE.Group。
* **性能**：人群使用 InstancedMesh；路径线条复用 BufferGeometry。
* **坐标**：Three.js 采用 Y 向上；后端网格 (x,y) → 前端 (x,z)。
* **交互**：manual 模式点击地面拾取点，POST 火点坐标后重启/重算。
* **UI**：ControlPanel.vue 切换模式与参数，FirePanel.vue 管火点与权重。

⠀
## 开发与运行步骤
### 初始化仓库
# 1) 克隆或新建
mkdir fire-evac-sim && cd fire-evac-sim
git init

# 2) 后端依赖（使用 Python 3.11）
uv init
uv python pin 3.11
uv add fastapi uvicorn rvo2 numpy pydantic pyyaml

# 3) 前端（使用 Bun）
bun create vite frontend --template vue-ts
cd frontend
bun install three pinia vue-router @types/three
cd ..

# 4) 运行
# 后端
uv run uvicorn backend.app.main:app --reload

# 前端（新终端）
cd frontend && bun run dev
### 环境变量（.env.example）
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173
SIM_TICK_HZ=20
LOG_LEVEL=INFO

## 测试与质量
* **后端**：pytest 覆盖 planner（A*）、rvo（基本避碰）、fire（代价场生成）。
* **前端**：基础 e2e（可选 Cypress）验证启动/连接/渲染。
* **格式化**：ruff/black（Python），eslint/prettier（TS）。

⠀
## 部署（最简单路径）
* **后端**：
  * 用 uv run fastapi + uvicorn，前置 nginx 做反向代理与 WebSocket 转发。
  * Docker 可选：基于 python:3.11-slim，在构建阶段编译 rvo2。
* **前端**：
  * bun run build 产出静态文件，nginx/CDN 托管。
  * 配置 VITE_BACKEND_URL 指向后端地址。

⠀
## 扩展路线（按优先级）
* 引入 FDS/烟雾场数据 → 以热图或体渲染叠加到 Three.js，代价场联动。
* APSO-FD 替换 A* 的全局路径候选生成（保持 RVO2 做局部避碰）。
* 多楼层/楼梯（NavMesh 或三维栅格）。
* 统计指标面板：平均疏散时间、瓶颈区域热力图、出口负载均衡度。
* 录制/回放（WebM / JSON 轨迹）。

⠀
## 常见问题（FAQ）
* **RVO2 在 Python 3.11 编译失败？** 安装 C++ 构建链（见“环境准备”）。若仍不成功：
  1 使用备选方案：rvo2-py（纯 Python 实现）或社会力模型；
  2 先上**纯 TS 路线**：前端用 pathfinding.js 做 A*，避障用简单规则或 ORCA 的 JS 实现；待后端可用时再切换回 RVO2。
* **Bun 安装问题？** 访问 https://bun.sh 获取最新安装指南。macOS/Linux: `curl -fsSL https://bun.sh/install | bash`
* **三维与网格对不上？** 确认 demo_map.json 的 cellSize 与 glTF 尺度一致；统一把后端 (x,y) 映射到 Three 的 (x,z)，高度 y 独立。
* **多人场景掉帧？** 代理使用 InstancedMesh；降低 tick_hz；只在关键帧推送路径，其他帧推送位置。
* **跨域问题？** FastAPI 开启 CORS，允许 http://localhost:5173；生产环境改为你的域名。

⠀
## 许可证与署名
* 默认 MIT（可改为你的组织要求）。
* 学术论文/演示请注明作者与仓库链接。

⠀
## 给 AI 的初始化提示（可复制给 Claude Code）
请按 README 中的目录结构在当前仓库生成项目骨架：
1 后端：FastAPI 入口、/sim/start、/sim/replan、/ws/sim/{id}；A* 的 planner.py、RVO2 封装 rvo.py、fire.py 代价场、grid.py 地图装载；读取 simulation.yaml；uv run uvicorn ... 运行。
2 前端：Vite + Vue + TS + Three.js；创建 SceneCanvas.vue、src/three/scene.ts、agents.ts、paths.ts、fire.ts；WS 连接后渲染代理、路径与火点。
3 保持坐标系约定（后端 (x,y) → 前端 (x,z)），并提供最小示例数据 demo_map.json 与 simulation.yaml。
