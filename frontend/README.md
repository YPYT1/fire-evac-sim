# 前端说明

- `src/main.ts`：应用入口，挂载 Pinia 与 Router。
- `src/router.ts` + `src/views/SimulationView.vue`：单页路由框架。
- `src/store/simStore.ts`：Pinia 状态管理。
- `src/api/client.ts`：REST + WebSocket 客户端封装。
- `src/components/`：`SceneCanvas`（含手动火点拾取）、`ControlPanel`、`StatusPanel`、`FirePanel` 等界面组件。
- `src/three/`：Three.js 场景、模型与可视化工具。
- `public/models/`：自建建筑模型占位文件，需替换为真实 glb。

运行开发服务器：`bun run dev`。
运行单元测试：`bun run test:unit`。
运行 E2E 测试：`bun run test:e2e`。
