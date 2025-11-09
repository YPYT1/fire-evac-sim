"""会话管理：负责仿真实例的生命周期与调度。"""

from __future__ import annotations

import asyncio
from datetime import datetime
import random
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Tuple

from ..core.config import FloorConfig, SimulationSettings
from ..core.schemas import FireSource, SimReplanRequest, SimStartRequest, SimStartResponse, SimStatusResponse
from ..sim.fire import build_cost_field, sample_random_fire_positions
from ..sim.evacuation import EvacuationSimulator
from ..sim.grid import Grid, load_grid
from ..sim.multilevel import MultiLevelPathPlanner
from ..sim.state import SimulationState
from ..sim.utils import world_to_grid

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


def _random_floor_fires(
    grid: Grid,
    floor_config: FloorConfig,
    rng: random.Random | None = None,
) -> list[FireSource]:
    """基于楼层配置生成随机火源"""
    if not floor_config.fire_zones:
        # 无指定区域，使用全局可行区域
        count_range = floor_config.fire_count_range
        count = rng.randint(count_range[0], count_range[1]) if rng else count_range[0]
        return sample_random_fire_positions(
            grid,
            count,
            floor_y=floor_config.height,
            intensity_range=(0.8, 1.3),
            rng=rng,
        )
    
    # 基于 fire_zones 生成
    fires: list[FireSource] = []
    count_range = floor_config.fire_count_range
    total_count = rng.randint(count_range[0], count_range[1]) if rng else count_range[0]
    
    for _ in range(total_count):
        zone = rng.choice(floor_config.fire_zones) if rng else floor_config.fire_zones[0]
        rect = zone.get("rect")
        if not rect or len(rect) != 4:
            continue
        
        x0, y0, w, h = rect
        # 在区域内随机选择可行单元
        candidates = []
        for dy in range(h):
            for dx in range(w):
                gx, gy = x0 + dx, y0 + dy
                if 0 <= gx < grid.width and 0 <= gy < grid.height:
                    if grid.cells[gy][gx].walkable:
                        candidates.append((gx, gy))
        
        if candidates:
            cell = rng.choice(candidates) if rng else candidates[0]
            wx = grid.origin[0] + (cell[0] + 0.5) * grid.cell_size
            wz = grid.origin[2] + (cell[1] + 0.5) * grid.cell_size
            intensity = rng.uniform(0.8, 1.3) if rng else 1.0
            fires.append(FireSource(
                position=(wx, floor_config.height, wz),
                intensity=intensity,
            ))
    
    return fires


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
        """创建仿真会话并启动后台循环（多楼层支持）。"""
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

        # 获取楼层配置
        floor_config = sim_settings.get_floor_config(floor_mode)
        if not floor_config:
            # Fallback 到旧配置
            floor_config = FloorConfig(
                name="默认楼层",
                height=0.0,
                grid_file=sim_settings.map_name,
                exits=[],
                spawn_regions=sim_settings.start_regions,
                fire_zones=[],
            )

        state = SimulationState(
            session_id=session_id,
            tick_hz=effective_tick_hz,
            goals=payload.goals,
            total_agents=payload.agents.count,
            fire_decay=fire_decay,
        )

        # 加载楼层专属地图
        maps_dir = Path(__file__).resolve().parents[1] / "data" / "maps"
        map_path = maps_dir / floor_config.grid_file
        if not map_path.exists():
            # Fallback 到默认地图
            map_path = maps_dir / sim_settings.map_name
        
        grid = load_grid(map_path)
        engine = EvacuationSimulator(grid)
        
        # 生成随机火源（基于楼层配置）
        rng = random.Random()
        random_fires = _random_floor_fires(grid, floor_config, rng)
        fires = payload.fires or random_fires
        if not fires:
            fires = random_fires
        state.fires = fires
        state.speed_mean = payload.agents.speed_mean
        state.speed_std = payload.agents.speed_std

        # 确定目标（出口或楼梯）
        goals = payload.goals
        if not goals:
            # 根据楼层确定目标
            if floor_config.exits:
                goals = [exit_cfg["id"] for exit_cfg in floor_config.exits]
            elif floor_config.stairs:
                # 如果是高层，目标是楼梯
                goals = floor_config.stairs
            else:
                goals = list(grid.exits.keys())
        state.goals = list(goals)
        
        blocked_cells = _blocked_cells_for_fires(grid, fires)
        cost_lookup = _cost_lookup(grid, fires, fire_decay)
        
        # 使用楼层配置的spawn_regions
        start_regions = floor_config.spawn_regions if floor_config.spawn_regions else sim_settings.start_regions
        
        spawned = engine.initialize_agents(
            payload.agents,
            start_regions,
            goals,
            floor_y=floor_config.height,
            blocked=blocked_cells,
            cost_field=cost_lookup,
            override_start=None,
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
