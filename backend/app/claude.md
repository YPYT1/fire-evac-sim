# backend/app 目录
- 定位：后端应用主包，组织 API、核心仿真与服务层。
- 包含内容：
  - `main.py` 创建 FastAPI 实例并挂载路由。
  - `api/` 管理 REST 与 WebSocket，`core/` 提供配置与 Pydantic 模型。
  - `sim/` 聚合仿真算法，`services/` 负责会话生命周期。
- 关联关系：
  - 依赖 `app/data/` 配置与地图，供 `backend/tests` 调用验证。
