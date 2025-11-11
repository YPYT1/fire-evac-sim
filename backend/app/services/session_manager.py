"""会话管理：负责仿真实例的生命周期与调度。"""

from __future__ import annotations

import asyncio
from datetime import datetime
import random
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Tuple

from ..core.config import CrowdBehaviorConfig, FloorConfig, SimulationSettings
from ..core.schemas import CrowdOverride, FireSource, SimReplanRequest, SimStartRequest, SimStartResponse, SimStatusResponse
from ..sim.fire import build_cost_field, sample_random_fire_positions
from ..sim.multilevel_evacuation import MultiLevelEvacuationSimulator
from ..sim.state import SimulationState
from ..sim.utils import grid_to_world, scatter_cells, world_to_grid

DEFAULT_MODE = "floor1"


def _resolve_active_spawn_floors(sim_settings: SimulationSettings, mode: str) -> list[str]:
    floors = sim_settings.floors or {}
    if not floors:
        return [mode]
    if mode in floors:
        return [mode]
    if "floor1" in floors:
        return ["floor1"]
    return [next(iter(floors))]


def _random_floor_fires(
    grid: Grid,
    floor_config: FloorConfig,
    rng: random.Random | None = None,
) -> list[FireSource]:
    """基于楼层配置生成随机火源"""
    rng = rng or random.Random()
    count_range = floor_config.fire_count_range
    total_count = rng.randint(count_range[0], count_range[1]) if count_range else 0
    if total_count <= 0:
        return []

    min_spacing = getattr(floor_config, "fire_min_spacing", 0)

    if not floor_config.fire_zones:
        return sample_random_fire_positions(
            grid,
            total_count,
            floor_y=floor_config.height,
            intensity_range=(0.8, 1.3),
            rng=rng,
            min_spacing=min_spacing,
        )

    candidates: list[tuple[int, int]] = []
    for zone in floor_config.fire_zones:
        rect = zone.get("rect")
        if not rect or len(rect) != 4:
            continue
        x0, y0, w, h = rect
        for dy in range(h):
            for dx in range(w):
                gx, gy = x0 + dx, y0 + dy
                if 0 <= gx < grid.width and 0 <= gy < grid.height:
                    if grid.cells[gy][gx].walkable:
                        candidates.append((gx, gy))

    if not candidates:
        return sample_random_fire_positions(
            grid,
            total_count,
            floor_y=floor_config.height,
            intensity_range=(0.8, 1.3),
            rng=rng,
            min_spacing=min_spacing,
        )

    selected = scatter_cells(candidates, total_count, min_spacing, rng)
    fires: list[FireSource] = []
    for gx, gy in selected:
        wx, _, wz = grid_to_world(gx, gy, grid.cell_size, grid.origin)
        intensity = rng.uniform(0.8, 1.3)
        fires.append(
            FireSource(
                position=(wx, floor_config.height, wz),
                intensity=intensity,
            )
        )

    return fires


def _blocked_cells_for_fires(
    grid,
    fires: list[FireSource],
    *,
    base_radius: int = 4,
    intensity_scale: float = 1.5,
) -> set[tuple[int, int]]:
    """根据火源生成禁行区域，半径会随火势强弱放大。"""

    blocked: set[tuple[int, int]] = set()
    for fire in fires:
        fx, _, fz = fire.position
        gx, gy = world_to_grid(fx, fz, grid.cell_size, grid.origin)
        radius = base_radius + int(max(0.0, fire.intensity - 1.0) * intensity_scale)
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


def _apply_crowd_override(
    sim_settings: SimulationSettings,
    override: CrowdOverride | None,
) -> SimulationSettings:
    if not override:
        return sim_settings
    base = sim_settings.crowd or CrowdBehaviorConfig()
    payload = base.model_dump()
    for key, value in override.model_dump(exclude_unset=True).items():
        if value is not None:
            payload[key] = value
    updated = CrowdBehaviorConfig(**payload)
    return sim_settings.model_copy(update={"crowd": updated})


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
        """创建仿真会话并启动后台循环（真正的多楼层支持）。"""
        self._counter += 1
        session_id = f"demo-{self._counter}"
        sim_settings = _apply_crowd_override(sim_settings, payload.crowd)
        tick_hz = sim_settings.tick_hz
        default_strategy = sim_settings.avoidance_strategy
        fire_decay = sim_settings.fire_decay
        strategy = payload.avoidance_strategy or default_strategy
        requested_scale = getattr(payload, "time_scale", 1.0) or 1.0
        time_scale = max(0.25, min(float(requested_scale), 4.0))
        effective_tick_hz = max(1.0, tick_hz * time_scale)
        floor_mode = payload.mode or sim_settings.mode or DEFAULT_MODE

        state = SimulationState(
            session_id=session_id,
            tick_hz=effective_tick_hz,
            goals=payload.goals,
            total_agents=payload.agents.count,
            fire_decay=fire_decay,
        )

        maps_dir = Path(__file__).resolve().parents[1] / "data" / "maps"
        
        # 使用多楼层引擎
        multilevel_engine = MultiLevelEvacuationSimulator(sim_settings, maps_dir)
        active_spawn_floors = _resolve_active_spawn_floors(sim_settings, floor_mode)
        multilevel_engine.set_active_spawn_floors(active_spawn_floors)

        default_target_floor = None
        if sim_settings.floors:
            if floor_mode == "floor1" or "floor1" not in sim_settings.floors:
                default_target_floor = floor_mode if floor_mode in sim_settings.floors else next(iter(sim_settings.floors))
            else:
                default_target_floor = "floor1"
        goal_override = payload.goals if payload.goals else None
        multilevel_engine.set_target_strategy(default_target_floor, goal_override)
        
        # 在所需楼层生成火源
        all_fires: List[FireSource] = []
        floor_fire_map: Dict[str, List[FireSource]] = {}
        blocked_by_floor: Dict[str, Set[Tuple[int, int]]] = {}
        cost_fields: Dict[str, Dict[Tuple[int, int], float]] = {}
        fire_levels: Set[str] = set(active_spawn_floors) if active_spawn_floors else set()
        if not fire_levels and floor_mode:
            fire_levels.add(floor_mode)

        if sim_settings.floors:
            rng = random.Random()
            for floor_id, floor_config in sim_settings.floors.items():
                grid = multilevel_engine.floor_grids.get(floor_id)
                if grid is None:
                    continue
                floor_fires: List[FireSource] = []
                if floor_id in fire_levels:
                    floor_fires = _random_floor_fires(grid, floor_config, rng)
                    all_fires.extend(floor_fires)
                floor_fire_map[floor_id] = floor_fires
                blocked_by_floor[floor_id] = _blocked_cells_for_fires(grid, floor_fires)
                cost_fields[floor_id] = _cost_lookup(grid, floor_fires, fire_decay)

        state.fires = all_fires
        state.speed_mean = payload.agents.speed_mean
        state.speed_std = payload.agents.speed_std

        multilevel_engine.set_floor_fires(floor_fire_map)

        # 初始化多楼层人员（按比例分配）
        spawned = multilevel_engine.initialize_agents_multilevel(
            total_count=payload.agents.count,
            agent_config=payload.agents,
            blocked_by_floor=blocked_by_floor,
            cost_fields=cost_fields,
            floor_fires=floor_fire_map,
        )
        
        state.total_agents = spawned
        state.set_agents(multilevel_engine.agent_states())
        
        # 获取跨层路径（用于可视化）
        state.paths = [[list(point) for point in path] for path in multilevel_engine.paths()]
        state.last_updated = datetime.utcnow()
        
        # 确定最终目标（一层出口）
        if multilevel_engine.target_goal_ids:
            state.goals = list(multilevel_engine.target_goal_ids)
        elif goal_override:
            state.goals = goal_override
        
        self._sessions[session_id] = {
            "payload": payload,
            "created_at": datetime.utcnow(),
            "tick_hz": tick_hz,
            "avoidance_strategy": strategy,
            "state": state,
            "fires": all_fires,
            "fire_decay": fire_decay,
            "engine": multilevel_engine,
            "floor_mode": floor_mode,
            "sim_settings": sim_settings,
            "blocked_by_floor": blocked_by_floor,
            "cost_fields": cost_fields,
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
        """更新会话火点数据，触发后续重规划（多楼层支持）。"""
        session = self._sessions.get(payload.session_id)
        if session is None:
            raise KeyError(payload.session_id)
        
        # 多楼层模式：保持火源原有的 y 坐标（楼层高度）
        normalized: list[FireSource] = []
        for fire in payload.fires:
            x, y, z = fire.position
            normalized.append(FireSource(position=(x, y, z), intensity=fire.intensity))
        
        session["fires"] = normalized
        state: SimulationState = session["state"]
        state.fires = normalized
        
        # 更新每层的阻塞区域和代价场
        sim_settings = session.get("sim_settings")
        if sim_settings and sim_settings.floors:
            engine = session.get("engine")
            if isinstance(engine, MultiLevelEvacuationSimulator):
                prev_blocked: Dict[str, Set[Tuple[int, int]]] = session.get("blocked_by_floor", {})
                blocked_by_floor: Dict[str, Set[Tuple[int, int]]] = {}
                cost_fields: Dict[str, Dict[Tuple[int, int], float]] = {}
                floor_fire_map: Dict[str, List[FireSource]] = {}
                changed_floors: Set[str] = set()
                
                for floor_id, floor_config in sim_settings.floors.items():
                    # 筛选该层的火源
                    floor_fires = [f for f in normalized if abs(f.position[1] - floor_config.height) < 0.5]
                    grid = engine.floor_grids.get(floor_id)
                    if grid:
                        blocked = _blocked_cells_for_fires(grid, floor_fires)
                        costs = _cost_lookup(grid, floor_fires, state.fire_decay)
                        blocked_by_floor[floor_id] = blocked
                        cost_fields[floor_id] = costs
                        floor_fire_map[floor_id] = floor_fires
                        if blocked != prev_blocked.get(floor_id):
                            changed_floors.add(floor_id)
                
                session["blocked_by_floor"] = blocked_by_floor
                session["cost_fields"] = cost_fields
                engine.update_navigation_fields(
                    blocked_by_floor,
                    cost_fields,
                    floor_fires=floor_fire_map or None,
                    affected_floors=changed_floors or None,
                )
                state.set_agents(engine.agent_states())
                state.paths = [[list(point) for point in path] for path in engine.paths()]
        
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
                engine: MultiLevelEvacuationSimulator | None = session.get("engine")
                if engine is None:
                    await asyncio.sleep(tick_interval)
                    continue
                engine.tick(tick_interval)
                state.set_agents(engine.agent_states())
                state.paths = [[list(point) for point in path] for path in engine.paths()]
                state.tick_count += 1
                state.last_updated = datetime.utcnow()
                await asyncio.sleep(tick_interval)

        loop = asyncio.get_event_loop()
        self._tasks[session_id] = loop.create_task(runner())


# 全局单例，后续可替换为依赖注入
session_manager = SessionManager()
