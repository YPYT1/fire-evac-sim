# frontend/src/store 目录
- 定位：Pinia 状态管理。
- 包含内容：
  - `simStore.ts` 维护会话 ID、代理与火源数据，并处理 WebSocket 消息。
- 关联关系：
  - 组件通过该 store 与 API/Three.js 交互。
