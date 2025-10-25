# 后端说明

`backend/app` 目录已按模块划分：
- `main.py`：FastAPI 入口，挂载 REST 与 WebSocket。
- `api/`：REST（`routes_sim.py`）与 WebSocket（`ws.py`）路由。
- `core/`：配置与 Pydantic 模型。
- `sim/`：网格、火源、规划、RVO2 等仿真核心占位实现。
- 配置文件 `app/core/config.py` 现支持 `avoidance_strategy`，可在 `simulation.yaml` 中选择 `rvo2`、`rvo2_py` 或 `simple`。
- `services/`：会话管理器，负责会话生命周期、异步 tick 循环以及火点重规划。
- `dependencies.py`：FastAPI Depends 入口，统一提供 `SessionManager` 等共享实例。
- `data/`：示例地图、配置与模型占位文件。

`backend/tests/` 与 `backend/scripts/` 目录提供单测占位与辅助脚本。具体实现细节请参考根目录 `TODO.md`。
- 集成测试：`tests/test_simulation_flow.py` 覆盖 `/sim/start → /sim/status → /sim/stop`。使用 `uv run pytest` 执行。
