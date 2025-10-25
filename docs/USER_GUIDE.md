# 用户使用手册

> 适用对象：项目演示人员、测试同学、建模同学。默认在本机（macOS / Ubuntu）运行。

---

## 1. 快速体验
1. 确认已执行 `uv sync` 与 `bun install`（详见 README 中的「本地快速开始」）。
2. 运行启动脚本（会自动检查并安装缺失的 Python、uv、Bun、Node.js，并优先从 `third_party/python-rvo2` 本地源码安装 RVO2 避障库）：
   - macOS: `./start_macos.sh`
   - Ubuntu: `./start_ubuntu.sh`
3. 浏览器访问 `http://localhost:5173`，控制面板点击「启动仿真」即可看到三维场景、人员与火点。
4. 若需查看实时日志，打开 `logs/backend.log`、`logs/frontend.log`。

---

## 2. 创建新场景（自建建筑模型）

| 步骤 | 操作 | 说明 |
|------|------|------|
| **2.1 建模** | 使用 Blender/SketchUp 导出 `.glb` 模型，放入 `frontend/public/models/building.glb`。 | 请保持坐标原点位于建筑地面左下角，单位为米。 |
| **2.2 坐标对齐** | 编辑 `frontend/public/models/building_alignment.json`。 | 调整 `model.offset/scale/rotation_y_deg`，并写入关键锚点（`anchors`）。 |
| **2.3 地图网格** | 在 `backend/app/data/maps/` 新建 JSON（可复制 `demo_map.json`）。 | `width`、`height` 与 `cellSize` 必须与建筑模型平面尺寸匹配。 |
| **2.4 仿真配置** | 更新 `backend/app/data/config/simulation.yaml` 中的 `map.file`、`agents`、`fire`。 | 可定义起始区域、出口矩形、火焰模式等。 |
| **2.5 校验** | 运行 `python scripts/integration_runner.py`。 | 启动时会自动验证坐标对齐，输出不一致项。 |

> 提示：若只需要调整人员数量或火焰参数，可直接编辑 `simulation.yaml` 并重启后端，无需重启前端。

---

## 3. 手动添加火点（Manual 模式）
1. 在控制面板选择「手动指定」模式，输入需要的人员数量。
2. 点击「启动仿真」后，Three.js 画布会切换为十字准星光标。
3. 单击场景任意地面，即可放置火点（最多 5 个，支持重复修改）。
4. 火点信息会通过 `/sim/replan` 写入后端，并驱动重新规划路径。
5. 使用状态面板可观察「拥堵率」「平均速度」等指标变化。

手动模式产生的火点序列会在 Pinia store 中维护，可通过点击控制面板的「停止仿真」清空。

---

## 4. 常见问题（FAQ）

### Q1. 前端页面空白或无数据？
- 确认启动脚本已运行，且 `logs/frontend.log` 没有构建错误。
- 检查 `.env.development` 或 `.env` 中的 `VITE_BACKEND_URL` 是否指向正在运行的后端。

### Q2. WebSocket 一直连接失败？
- 确认后端输出中存在 `Uvicorn running on http://127.0.0.1:8000`。
- 在浏览器地址栏访问 `http://127.0.0.1:8000/docs`，若无法打开则后端未启动。
- 若端口被占用，可在 `start_*` 脚本中修改 `BACKEND_HOST/BACKEND_PORT` 环境变量。

### Q3. 新模型坐标错位？
- 使用 `scripts/integration_runner.py` 查看「坐标对齐验证」输出。
- 重点检查 `building_alignment.json` 的 `anchors`，确保 `grid` 坐标换算正确。

### Q4. 人群拥堵率始终为 0？
- 在 `simulation.yaml` 中确认 `agents.count` 是否大于 0。
- 确保状态面板在运行过程中收到 WebSocket 帧，可观察 `logs/backend.log` 中的广播频率。

### Q5. 启动脚本卡住或看不到前端？
- 等待依赖安装完成（首次运行会自动执行 `bun install` / `uv sync`）。
- 若仍无响应，可手动在两个终端上分别运行后端与前端命令。

---

## 5. 日志与排错
- 所有一键脚本日志默认写入 `logs/backend.log`、`logs/frontend.log`。
- 若需要更详细的后端日志，可在脚本中设置 `LOG_LEVEL=DEBUG`。
- 压力测试输出位于 `stress_report.json`（可通过 `STRESS_REPORT_PATH` 自定义）。
- 测试命令：
  ```bash
  uv run pytest
  bun run lint
  bun run test:unit:run
  ```

---

## 6. 参考资料
- `README.md`：项目概览、技术栈、扩展路线。
- `docs/INTEGRATION.md`：联调脚本使用说明。
- `docs/STRESS_TEST.md`：极端场景压力测试指南。
- `frontend/src/components/StatusPanel.vue`：实时状态指标显示逻辑。
