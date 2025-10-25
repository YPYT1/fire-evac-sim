# backend/app/data/maps 目录
- 定位：保存地图与网格数据文件。
- 包含内容：
  - `demo_map.json` 作为占位场景，未来可替换为真实建筑平面转换成果。
- 关联关系：
  - 供 `sim/grid.py` 加载，并与前端 Three.js 模型保持一致。
