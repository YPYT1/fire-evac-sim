# backend 目录
- 定位：承载 FastAPI 后端工程与配套脚本。
- 包含内容：
  - `app/` 内含应用代码，`tests/` 放置 pytest 用例，`scripts/` 提供开发辅助脚本。
  - 根下 `README.md` 概览模块职责。
  - 使用根级 `pyproject.toml` 管理依赖与工具链。
- 关联关系：
  - 与 `frontend` 通过 REST/WebSocket 交互，配置引用 `docs/` 与根级 .env。
