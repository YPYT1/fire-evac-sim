# backend/app/data/config 目录
- 定位：维护仿真参数配置文件。
- 包含内容：
  - `simulation.yaml` 定义模式、tick 频率、代理数量等默认值。
- 关联关系：
  - 由 `core.config` 读取，影响服务层与仿真模块的默认行为。
