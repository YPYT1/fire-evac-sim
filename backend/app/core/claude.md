# backend/app/core 目录
- 定位：存放配置读取与公共数据模型。
- 包含内容：
  - `config.py` 加载环境变量与 YAML 配置，提供 Settings 单例。
  - `schemas.py` 定义启动、重规划、状态等 Pydantic 模型。
- 关联关系：
  - 被 API、服务层与仿真模块广泛引用，是依赖注入的基础。
