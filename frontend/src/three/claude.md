# frontend/src/three 目录
- 定位：Three.js 场景与可视化工具封装。
- 包含内容：
  - `scene.ts` 初始化渲染环境，`agents.ts` / `fire.ts` / `paths.ts` 管理实例化对象。
  - `loaders.ts` 加载 glb 资源，`models/` 存放自建模型脚本。
- 关联关系：
  - 供组件调用，依赖 Pinia 数据与 public 模型资产。
