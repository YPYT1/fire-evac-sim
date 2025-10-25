# frontend/src/components 目录
- 定位：组合式 UI 组件集合。
- 包含内容：
  - `SceneCanvas.vue` 渲染 Three 场景。
  - `ControlPanel.vue` 控制仿真生命周期。
  - `FirePanel.vue` 管理火源信息。
- 关联关系：
  - 与 `store` 同步状态，调用 `api`，并使用 `three` 模块渲染。
