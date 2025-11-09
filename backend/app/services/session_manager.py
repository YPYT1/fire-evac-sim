"""会话管理：负责仿真实例的生命周期与调度。"""

from __future__ import annotations

import asyncio
from datetime import datetime
import random
from pathlib import Path
from typing import Dict, Literal, Optional

from ..core.config import SimulationSettings
from ..core.schemas import FireSource, SimReplanRequest, SimStartRequest, SimStartResponse, SimStatusResponse
from ..sim.fire import build_cost_field, sample_random_fire_positions
from ..sim.evacuation import EvacuationSimulator
from ..sim.grid import load_grid
from ..sim.state import SimulationState
from ..sim.utils import world_to_grid

FLOOR_HEIGHT = 4.0
FLOOR_CONFIGS = {
    "floor1": {
        "name": "一层",
        "floor_y": 0.0,
        "fires": [],
        "random_fire": {"count": 2, "intensity_range": (0.9, 1.4)},
        "spawn_area": None,
    },
    "floor2": {
        "name": "二层",
        "floor_y": FLOOR_HEIGHT,
        "fires": [],
        "random_fire": {"count": 2, "intensity_range": (0.9, 1.3)},
        "spawn_area": {"center": (-10.0, 0.0), "width": 10, "depth": 18},
    },
    "floor3": {
        "name": "三层",
        "floor_y": FLOOR_HEIGHT * 2,
        "fires": [],
        "random_fire": {"count": 3, "intensity_range": (0.95, 1.35)},
        "spawn_area": {"center": (10.0, 0.0), "width": 10, "depth": 18},
    },
}
DEFAULT_MODE = "floor1"


def _build_floor_fires(config: dict) -> list[FireSource]:
    floor_y = float(config.get("floor_y", 0.0))
    fires: list[FireSource] = []
    for fire in config.get("fires", []):
        position = fire.get("position", (0.0, 0.0))
        if len(position) != 2:
            continue
        x, z = float(position[0]), float(position[1])
        intensity = float(fire.get("intensity", 1.0))
        fires.append(FireSource(position=(x, floor_y, z), intensity=intensity))
    return fires


def _random_floor_fires(grid, config: dict, floor_y: float) -> list[FireSource]:
    random_cfg = config.get("random_fire")
    if not random_cfg:
        return []
    count = max(1, int(random_cfg.get("count", 1)))
    intensity_cfg = random_cfg.get("intensity_range", (1.0, 1.2))
    if isinstance(intensity_cfg, (list, tuple)) and len(intensity_cfg) >= 2:
        min_intensity = float(intensity_cfg[0])
        max_intensity = float(intensity_cfg[1])
    else:
        value = float(intensity_cfg)
        min_intensity = value
        max_intensity = value
    seed = random_cfg.get("seed")
    rng = random.Random(seed) if seed is not None else random.Random()
    return sample_random_fire_positions(
        grid,
        count,
        floor_y=floor_y,
        intensity_range=(min_intensity, max_intensity),
        rng=rng,
    )


def _blocked_cells_for_fires(grid, fires: list[FireSource], radius: int = 3) -> set[tuple[int, int]]:
    blocked: set[tuple[int, int]] = set()
    for fire in fires:
        fx, _, fz = fire.position
        gx, gy = world_to_grid(fx, fz, grid.cell_size, grid.origin)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < grid.width and 0 <= ny < grid.height:
                    blocked.add((nx, ny))
    return blocked


def _cost_lookup(grid, fires: list[FireSource], decay: float) -> Dict[tuple[int, int], float]:
    if not fires:
        return {}
    field = build_cost_field(grid, fires, decay)
    lookup: Dict[tuple[int, int], float] = {}
    for y in range(grid.height):
        for x in range(grid.width):
            lookup[(x, y)] = float(field[y, x]) - 1.0  # baseline 1.0 removed
    return lookup


def _spawn_cells_from_area(
    grid,
    origin_center: tuple[float, float],
    width: int,
    depth: int,
    *,
    blocked: Optional[set[tuple[int, int]]] = None,
) -> list[tuple[int, int]]:
    cx, cz = origin_center
    gx, gy = world_to_grid(cx, cz, grid.cell_size, grid.origin)
    half_w = max(1, width // 2)
    half_d = max(1, depth // 2)
    cells: list[tuple[int, int]] = []
    for dz in range(-half_d, half_d + 1):
        for dx in range(-half_w, half_w + 1):
            nx, ny = gx + dx, gy + dz
            if 0 <= nx < grid.width and 0 <= ny < grid.height:
                if grid.cells[ny][nx].walkable and (not blocked or (nx, ny) not in blocked):
                    cells.append((nx, ny))
    return cells


class SessionManager:
    """管理仿真会话、后台循环与火点更新。"""

    def __init__(self) -> None:
        self._sessions: Dict[str, dict] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._counter: int = 0

    def start(
        self,
        payload: SimStartRequest,
        sim_settings: SimulationSettings,
    ) -> SimStartResponse:
        """创建仿真会话并启动后台循环。"""
        self._counter += 1
        session_id = f"demo-{self._counter}"
        tick_hz = sim_settings.tick_hz
        default_strategy = sim_settings.avoidance_strategy
        fire_decay = sim_settings.fire_decay
        strategy = payload.avoidance_strategy or default_strategy
        requested_scale = getattr(payload, "time_scale", 1.0) or 1.0
        time_scale = max(0.25, min(float(requested_scale), 4.0))
        effective_tick_hz = max(1.0, tick_hz * time_scale)
        floor_mode = payload.mode or sim_settings.mode or DEFAULT_MODE
        floor_config = FLOOR_CONFIGS.get(floor_mode, FLOOR_CONFIGS[DEFAULT_MODE])
        floor_y = float(floor_config.get("floor_y", 0.0))

        state = SimulationState(
            session_id=session_id,
            tick_hz=effective_tick_hz,
            goals=payload.goals,
            total_agents=payload.agents.count,
            fire_decay=fire_decay,
        )
        map_path = Path(__file__).resolve().parents[1] / "data" / "maps" / sim_settings.map_name
        grid = load_grid(map_path)
        engine = EvacuationSimulator(grid)
        default_fires = _build_floor_fires(floor_config)
        random_fires = _random_floor_fires(grid, floor_config, floor_y)
        base_fires: list[FireSource] = list(default_fires)
        if random_fires:
            base_fires.extend(random_fires)
        fires = payload.fires or base_fires
        if not fires:
            fires = random_fires or default_fires
        state.fires = fires
        state.speed_mean = payload.agents.speed_mean
        state.speed_std = payload.agents.speed_std

        goals = payload.goals or sim_settings.goals
        if not goals:
            goals = list(grid.exits.keys())
        state.goals = list(goals)
        blocked_cells = _blocked_cells_for_fires(grid, fires)
        cost_lookup = _cost_lookup(grid, fires, fire_decay)
        spawn_cfg = floor_config.get("spawn_area")
        override_start = None
        start_regions = sim_settings.start_regions
        if spawn_cfg:
            center = spawn_cfg.get("center", (0.0, 0.0))
            width = int(spawn_cfg.get("width", 4))
            depth = int(spawn_cfg.get("depth", 8))
            override_start = _spawn_cells_from_area(
                grid,
                (float(center[0]), float(center[1])),
                width,
                depth,
                blocked=blocked_cells,
            ) or None
            start_regions = []  # 楼层出生点单独指定
        spawned = engine.initialize_agents(
            payload.agents,
            start_regions,
            goals,
            floor_y=floor_y,
            blocked=blocked_cells,
            cost_field=cost_lookup,
            override_start=override_start,
        )
        state.total_agents = spawned
        state.set_agents(engine.agent_states())
        state.paths = [[list(point) for point in path] for path in engine.paths()]
        state.last_updated = datetime.utcnow()

        self._sessions[session_id] = {
            "payload": payload,
            "created_at": datetime.utcnow(),
            "tick_hz": tick_hz,
            "avoidance_strategy": strategy,
            "state": state,
            "fires": fires,
            "fire_decay": fire_decay,
            "engine": engine,
            "grid": grid,
            "floor_mode": floor_mode,
            "floor_y": floor_y,
            "floor_config": floor_config,
            "blocked_cells": blocked_cells,
            "cost_lookup": cost_lookup,
        }
        self._start_loop(session_id, state)
        return SimStartResponse(session_id=session_id, tick_hz=state.tick_hz, avoidance_strategy=strategy)

    def status(self, session_id: str) -> SimStatusResponse:
        """返回仿真当前状态指标。"""
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        state: SimulationState = session["state"]
        stats = state.stats()
        return SimStatusResponse(
            session_id=session_id,
            agent_count=state.total_agents,
            active_agents=stats["active_agents"],
            average_speed=stats["average_speed"],
            congestion_ratio=stats["congestion_ratio"],
            updated_at=state.last_updated,
            avoidance_strategy=session.get("avoidance_strategy", "rvo2"),
            tick_hz=state.tick_hz,
            speed_mean=stats["speed_mean"],
            speed_std=stats["speed_std"],
            fire_decay=stats["fire_decay"],
        )

    def stop(self, session_id: str) -> None:
        """终止会话并取消后台任务。"""
        self._sessions.pop(session_id, None)
        task = self._tasks.pop(session_id, None)
        if task:
            task.cancel()

    def replan(self, payload: SimReplanRequest) -> None:
        """更新会话火点数据，触发后续重规划。"""
        session = self._sessions.get(payload.session_id)
        if session is None:
            raise KeyError(payload.session_id)
        floor_y = float(session.get("floor_y", 0.0))
        grid = session.get("grid")
        normalized: list[FireSource] = []
        for fire in payload.fires:
            x, _, z = fire.position
            normalized.append(FireSource(position=(x, floor_y, z), intensity=fire.intensity))
        session["fires"] = normalized
        state: SimulationState = session["state"]
        state.fires = normalized
        if grid is not None:
            session["blocked_cells"] = _blocked_cells_for_fires(grid, normalized)
            session["cost_lookup"] = _cost_lookup(grid, normalized, state.fire_decay)
        session.setdefault("replans", []).append(payload)

    def get_state(self, session_id: str) -> Optional[SimulationState]:
        """提供给 WebSocket 层的快照读取接口。"""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        return session["state"]

    def _start_loop(self, session_id: str, state: SimulationState) -> None:
        async def runner() -> None:
            tick_interval = 1 / state.tick_hz
            while session_id in self._sessions:
                session = self._sessions.get(session_id)
                if session is None:
                    break
                engine: EvacuationSimulator | None = session.get("engine")
                if engine is None:
                    await asyncio.sleep(tick_interval)
                    continue
                engine.step(tick_interval)
                state.set_agents(engine.agent_states())
                state.paths = [[list(point) for point in path] for path in engine.paths()]
                state.tick_count += 1
                state.last_updated = datetime.utcnow()
                await asyncio.sleep(tick_interval)

        loop = asyncio.get_event_loop()
        self._tasks[session_id] = loop.create_task(runner())


# 全局单例，后续可替换为依赖注入
session_manager = SessionManager()
