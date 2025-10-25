# 依赖管理记录

## 后端（uv）
- 已安装：`fastapi`、`uvicorn`、`numpy`、`pydantic`、`pyyaml`。
- 待确认：`python-rvo2`（PyPI 暂未检索到，同类包名称可能为 `rvo2` 或需从源码构建）。当前代码可通过 `SimulationSettings.avoidance_strategy` 切换为 `rvo2_py` 或 `simple` fallback，在缺失原生依赖时能够继续运行占位仿真。

> 操作命令：
> ```bash
> uv init
> uv python pin 3.11
> uv add fastapi uvicorn numpy pydantic pyyaml
> ```

## 前端（Bun）
- 计划在阶段 0-5 初始化，安装 `vue`、`pinia`、`vue-router`、`three`、`@types/three` 等依赖。

后续若新增依赖，请记录命令与原因，保持与 `TODO.md` 同步。
