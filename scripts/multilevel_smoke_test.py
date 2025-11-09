#!/usr/bin/env python3
"""简单的多楼层仿真烟雾测试：验证火点/人员随机性与出口分流。"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - 仅用于友好提示
    import yaml  # type: ignore # noqa: F401
except ModuleNotFoundError as exc:  # pragma: no cover
    print("缺少 PyYAML，请在可访问 PyPI 的环境执行 `pip3 install pyyaml` 后重试此脚本。")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.config import (  # noqa: E402
    CrowdBehaviorConfig,
    SimulationSettings,
    load_simulation_config,
)
from backend.app.core.schemas import AgentSpawnConfig  # noqa: E402
from backend.app.services.session_manager import (  # noqa: E402
    _cost_lookup,
    _random_floor_fires,
    _blocked_cells_for_fires,
)
from backend.app.sim.multilevel_evacuation import MultiLevelEvacuationSimulator  # noqa: E402
from backend.app.sim.utils import world_to_grid  # noqa: E402


def infer_floor(y: float, floors) -> str:
    best = None
    best_delta = float('inf')
    for floor_id, cfg in floors.items():
        delta = abs(cfg.height - y)
        if delta < best_delta:
            best_delta = delta
            best = floor_id
    return best or 'floor1'


def summarize(engine: MultiLevelEvacuationSimulator, floors) -> dict:
    floor_counts = Counter()
    spawn_cells: Dict[str, set] = defaultdict(set)
    for agent in engine.agents.values():
        if not agent.path:
            continue
        floor_id = infer_floor(agent.path[0][1], floors)
        floor_counts[floor_id] += 1
        grid = engine.floor_grids.get(floor_id)
        if grid:
            gx, gy = world_to_grid(agent.path[0][0], agent.path[0][2], grid.cell_size, grid.origin)
            spawn_cells[floor_id].add((gx, gy))

    exit_counts = Counter(engine.agent_targets.values())
    path_lengths = [len(agent.path) for agent in engine.agents.values() if agent.path]
    return {
        'floor_counts': dict(floor_counts),
        'exit_counts': dict(exit_counts),
        'spawn_variety': {floor: len(cells) for floor, cells in spawn_cells.items()},
        'avg_path_len': statistics.fmean(path_lengths) if path_lengths else 0.0,
    }


def run_iteration(iteration: int, sim_settings, maps_dir: Path, seed: int) -> dict:
    engine = MultiLevelEvacuationSimulator(sim_settings, maps_dir)
    rng = random.Random(seed)
    floor_fires = {}
    blocked = {}
    costs = {}
    for floor_id, floor_cfg in (sim_settings.floors or {}).items():
        grid = engine.floor_grids[floor_id]
        fires = _random_floor_fires(grid, floor_cfg, rng)
        floor_fires[floor_id] = fires
        blocked[floor_id] = _blocked_cells_for_fires(grid, fires)
        costs[floor_id] = _cost_lookup(grid, fires, sim_settings.fire_decay)

    agent_cfg = AgentSpawnConfig(
        count=sim_settings.agent_count,
        speed_mean=sim_settings.speed_mean,
        speed_std=sim_settings.speed_std,
    )

    engine.initialize_agents_multilevel(
        sim_settings.agent_count,
        agent_cfg,
        blocked_by_floor=blocked,
        cost_fields=costs,
        floor_fires=floor_fires,
    )

    # 让人群推进几步以触发避障与跨层运动
    dt = 1.0 / sim_settings.tick_hz
    for _ in range(int(sim_settings.tick_hz * 2)):
        engine.tick(dt)

    summary = summarize(engine, sim_settings.floors or {})
    summary['iteration'] = iteration
    return summary


def apply_overrides(settings: SimulationSettings, args: argparse.Namespace) -> SimulationSettings:
    overrides: dict[str, object] = {}
    crowd_updates: dict[str, float] = {}
    if args.avoidance:
        overrides["avoidance_strategy"] = args.avoidance
    if args.crowd_radius is not None:
        crowd_updates["repulsion_radius"] = args.crowd_radius
    if args.crowd_gain is not None:
        crowd_updates["repulsion_gain"] = args.crowd_gain
    if args.crowd_push is not None:
        crowd_updates["repulsion_push_strength"] = args.crowd_push
    if crowd_updates:
        base = settings.crowd or CrowdBehaviorConfig()
        crowd = base.model_copy(update=crowd_updates)
        overrides["crowd"] = crowd
    if overrides:
        return settings.model_copy(update=overrides)
    return settings


def main() -> None:
    parser = argparse.ArgumentParser(description='多楼层仿真烟雾测试')
    parser.add_argument('-c', '--config', type=Path, default=ROOT / 'backend/app/data/config/simulation.yaml', help='配置文件路径')
    parser.add_argument('-n', '--iterations', type=int, default=3, help='迭代次数')
    parser.add_argument('--seed', type=int, default=2025, help='随机种子基础值')
    parser.add_argument('--avoidance', choices=['rvo2', 'rvo2_py', 'simple'], help='覆盖默认避障策略')
    parser.add_argument('--crowd-radius', type=float, help='覆盖 crowd.repulsion_radius')
    parser.add_argument('--crowd-gain', type=float, help='覆盖 crowd.repulsion_gain')
    parser.add_argument('--crowd-push', type=float, help='覆盖 crowd.repulsion_push_strength')
    args = parser.parse_args()

    settings = load_simulation_config(args.config.resolve())
    settings = apply_overrides(settings, args)
    maps_dir = ROOT / 'backend' / 'app' / 'data' / 'maps'

    if not settings.floors:
        raise SystemExit('配置未定义 floors，无法执行烟雾测试。')

    for i in range(args.iterations):
        summary = run_iteration(i + 1, settings, maps_dir, args.seed + i * 13)
        print(f"迭代 #{summary['iteration']}")
        print('  楼层人数分配:', summary['floor_counts'])
        print('  出口使用统计:', summary['exit_counts'])
        print('  唯一出生格:', summary['spawn_variety'])
        print(f"  平均路径节点: {summary['avg_path_len']:.1f}")
        print('-' * 48)


if __name__ == '__main__':
    main()
