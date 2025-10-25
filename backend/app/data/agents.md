# backend/app/data 目录
- 定位：集中存放后端运行所需的静态数据与示例资源。
- 包含内容：
  - `maps/` 包含 demo_map.json 栅格示例。
  - `models/` 放置自建建筑 glb 占位。
  - `config/` 提供 simulation.yaml 默认参数。
- 关联关系：
  - 被 `core.config` 与 `sim` 模块加载，需与前端 `public/models` 对齐。
