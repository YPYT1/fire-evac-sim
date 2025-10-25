# backend/app/sim 目录
- 定位：仿真核心算法的占位实现。
- 包含内容：
  - `grid.py` 解析栅格地图，`planner.py` 实现 A*。
  - `fire.py` 生成火源代价场，`rvo.py` 封装 RVO2，`state.py` 维护内存态。
  - `utils.py` 负责坐标转换等通用方法。
- 关联关系：
  - 与 `services.session_manager` 协作管理仿真状态，未来输出给 API/WebSocket。
