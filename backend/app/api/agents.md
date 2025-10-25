# backend/app/api 目录
- 定位：定义所有对外暴露的 REST 与 WebSocket 接口。
- 包含内容：
  - `routes_sim.py` 提供 /sim/* 控制接口。
  - `ws.py` 维护 `/ws/sim/{session_id}` 的实时推送骨架。
- 关联关系：
  - 依赖 `core.config`/`core.schemas` 注入配置，调用 `services.session_manager` 获取状态。
