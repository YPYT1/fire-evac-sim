# 压力测试记录

脚本位置：`scripts/stress_probe.py`。在后端服务启动后运行：

```bash
# 另一个终端已运行 uvicorn
uv run uvicorn backend.app.main:app --reload

# 压力测试（默认生成 stress_report.json）
python scripts/stress_probe.py
```

脚本会执行两类极端场景：

- **crowd_peak**：600 名代理同时疏散，用于观察高密度人群时的调度性能。
- **exit_blocked**：在出口附近投放高强度火源，模拟出口阻塞后的滞留与拥堵。

每个场景会定期轮询 `/sim/status`，记录响应延迟、拥堵率与平均速度，并将汇总写入 `stress_report.json`（可通过环境变量 `STRESS_REPORT_PATH` 自定义输出路径）。

若 `congestion_peak` ≥ 0.8 或 `latency_p95_ms` ≥ 120，则建议调低 `tick_hz`、优化规划策略或拆分会话，以防极端场景发生性能退化。
