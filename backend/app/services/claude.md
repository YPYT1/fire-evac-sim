# backend/app/services 目录
- 定位：封装服务层逻辑，如会话管理与后台任务。
- 包含内容：
  - `session_manager.py` 当前提供内存会话占位实现，后续将扩展事件驱动。
- 关联关系：
  - 被 API 层调用，同时驱动 `sim` 模块进行状态更新。
