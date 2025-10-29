"""联调脚本：调用后端 API 模拟多场景，并校验坐标对齐。(Stage 3-1/3-2)"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx

from backend.app.sim.utils import grid_to_world

BASE_URL = os.environ.get("SIM_BASE_URL", "http://127.0.0.1:8000")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = PROJECT_ROOT / "backend" / "app" / "data" / "maps" / "canteen_map.json"
ALIGNMENT_PATH = PROJECT_ROOT / "frontend" / "public" / "models" / "building_alignment.json"

SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "floor1-basic",
        "payload": {
            "mode": "floor1",
            "agents": {"count": 60, "speed_mean": 1.3, "speed_std": 0.15},
            "goals": ["north_door", "south_door"],
        },
    },
    {
        "name": "floor2-replan",
        "payload": {
            "mode": "floor2",
            "agents": {"count": 120, "speed_mean": 1.2, "speed_std": 0.25},
            "goals": ["east_door", "west_door"],
        },
        "replan_after": 2.0,
    },
    {
        "name": "floor3-custom",
        "payload": {
            "mode": "floor3",
            "agents": {"count": 90, "speed_mean": 1.4, "speed_std": 0.2},
            "goals": ["north_door"],
        },
        "manual_fires": [
            {"position": [-5.0, 8.0, 4.0], "intensity": 1.0},
            {"position": [12.0, 8.0, -6.0], "intensity": 0.9},
        ],
    },
]


def verify_coordinate_alignment() -> bool:
    print("\n▶ Running coordinate alignment check")
    if not MAP_PATH.exists():
        print(f"✖ 缺少地图文件：{MAP_PATH}")
        return False
    if not ALIGNMENT_PATH.exists():
        print(f"✖ 缺少对齐文件：{ALIGNMENT_PATH}")
        return False

    map_data = json.loads(MAP_PATH.read_text())
    alignment = json.loads(ALIGNMENT_PATH.read_text())

    issues: list[str] = []
    grid_meta = alignment.get("grid", {})
    model_meta = alignment.get("model", {})
    anchors = alignment.get("anchors", [])

    cell_size = float(map_data["cellSize"])
    origin_raw = map_data.get("origin", [0.0, 0.0, 0.0])
    origin = (float(origin_raw[0]), float(origin_raw[1]), float(origin_raw[2]))
    width_cells = int(map_data["width"])
    height_cells = int(map_data["height"])

    meta_width = int(grid_meta.get("width", width_cells))
    meta_height = int(grid_meta.get("height", height_cells))
    meta_cell = float(grid_meta.get("cell_size", cell_size))

    if meta_width != width_cells:
        issues.append(f"网格宽度不一致：后端={width_cells}，元数据={meta_width}")
    if meta_height != height_cells:
        issues.append(f"网格高度不一致：后端={height_cells}，元数据={meta_height}")
    if abs(meta_cell - cell_size) > 1e-6:
        issues.append(f"网格单元大小不一致：后端={cell_size}，元数据={meta_cell}")

    model_bounds = model_meta.get("bounds", {})
    min_bound = model_bounds.get("min", [0.0, 0.0, 0.0])
    max_bound = model_bounds.get("max", [0.0, 0.0, 0.0])
    span_x = float(max_bound[0]) - float(min_bound[0])
    span_z = float(max_bound[2]) - float(min_bound[2])
    expected_x = width_cells * cell_size
    expected_z = height_cells * cell_size

    if abs(span_x - expected_x) > 1e-3:
        issues.append(f"模型 X 方向范围 {span_x:.2f} 与网格 {expected_x:.2f} 不符")
    if abs(span_z - expected_z) > 1e-3:
        issues.append(f"模型 Z 方向范围 {span_z:.2f} 与网格 {expected_z:.2f} 不符")

    for anchor in anchors:
        label = anchor.get("id", "unknown_anchor")
        grid_pt = anchor.get("grid")
        world_pt = anchor.get("world")
        if not grid_pt or not world_pt:
            issues.append(f"{label} 缺少 grid/world 定义")
            continue

        gx, gy = float(grid_pt[0]), float(grid_pt[1])
        computed = grid_to_world(gx, gy, cell_size, origin)
        diff = max(abs(computed[0] - float(world_pt[0])), abs(computed[2] - float(world_pt[2])))
        if diff > 1e-3:
            issues.append(
                f"{label} 对齐误差过大：grid={grid_pt} → world={computed}，期望={world_pt}"
            )
    if not issues:
        print("  坐标对齐验证通过 ✅")
        return True

    print("  坐标对齐验证存在问题：")
    for item in issues:
        print(f"   - {item}")
    return False


async def run_scenario(client: httpx.AsyncClient, scenario: dict[str, Any]) -> None:
    name = scenario["name"]
    payload = scenario["payload"]
    print(f"\n▶ Running scenario: {name}")

    start_resp = await client.post("/sim/start", json=payload)
    start_resp.raise_for_status()
    data = start_resp.json()
    session_id = data["session_id"]
    tick_hz = data["tick_hz"]
    print(f"  session_id={session_id}, tick_hz={tick_hz}")

    await asyncio.sleep(1.0)

    status = await client.get("/sim/status", params={"session_id": session_id})
    status.raise_for_status()
    status_data = status.json()
    print(
        "  status: tick_hz={tick_hz}, active_agents={active_agents}, avg_speed={average_speed:.2f}, congestion={congestion_ratio:.2%}, fire_decay={fire_decay:.2f}".format(
            **status_data
        )
    )

    if scenario.get("replan_after"):
        await asyncio.sleep(float(scenario["replan_after"]))
        print("  triggering random replan")
        await client.post(
            "/sim/replan",
            json={
                "session_id": session_id,
                "fires": [],
                "reason": "random_reset",
            },
        )

    if scenario.get("manual_fires"):
        print("  posting manual fires")
        await client.post(
            "/sim/replan",
            json={
                "session_id": session_id,
                "fires": scenario["manual_fires"],
                "reason": "manual_test",
            },
        )
        await asyncio.sleep(1.0)

    stop = await client.post("/sim/stop", json={"session_id": session_id})
    stop.raise_for_status()
    print(f"  stopped session {session_id}")


async def main() -> None:
    verify_coordinate_alignment()
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        for scenario in SCENARIOS:
            try:
                await run_scenario(client, scenario)
            except httpx.HTTPError as exc:
                print(f"✖ Scenario {scenario['name']} failed: {exc}")
                break


if __name__ == "__main__":
    asyncio.run(main())
