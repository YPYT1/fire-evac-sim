# 联调脚本使用指南

本脚本用于阶段 3 的后端联调验证，依赖后端服务已在本地运行（默认 `http://127.0.0.1:8000`）。

## 脚本位置
`scripts/integration_runner.py`

## 使用方法
```bash
# 启动后端（需另开终端）
uv run uvicorn backend.app.main:app --reload

# 运行联调脚本
python scripts/integration_runner.py
```

可通过环境变量自定义后端地址：
```bash
SIM_BASE_URL=http://192.168.1.10:8000 python scripts/integration_runner.py
```

脚本会依次执行三类场景：
1. `fixed-basic`：固定火源 + 多出口。
2. `random-evac`：随机火源，模拟 replan 调用。
3. `manual-test`：手动火点列表，验证 `/sim/replan` 手动模式。

每个场景完成后会调用 `/sim/status` 输出关键指标，并最终 `/sim/stop` 停止会话。

## 坐标对齐校验

脚本启动时会自动加载：

- `backend/app/data/maps/demo_map.json`
- `frontend/public/models/building_alignment.json`

若网格宽度、高度、单元大小或锚点坐标存在偏差，脚本会输出失败原因。请在更新模型或地图后同步维护 `building_alignment.json` 以维持前后端坐标一致性。

在完成基础联调后，可执行 `scripts/stress_probe.py`（详见 `docs/STRESS_TEST.md`）评估极端人流与出口阻塞场景的性能瓶颈。
