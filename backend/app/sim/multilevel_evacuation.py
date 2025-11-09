"""多楼层疏散仿真引擎：整合楼层地图、楼梯路径与跨层运动。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..core.config import FloorConfig, SimulationSettings
from ..core.schemas import AgentSpawnConfig, AgentState
from .grid import Grid, load_grid
from .multilevel import MultiLevelPathPlanner
from .utils import world_to_grid

GridCoord = Tuple[int, int]
WorldCoord = Tuple[float, float, float]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


@dataclass
class MultiLevelAgent:
    """跨楼层代理，用离散路径推进。"""

    id: int
    path: List[WorldCoord]
    speed: float
    position: WorldCoord
    velocity: WorldCoord = (0.0, 0.0, 0.0)
    segment_index: int = 0
    finished: bool = False

    def step(self, dt: float) -> None:
        if self.finished or len(self.path) < 2:
            self.velocity = (0.0, 0.0, 0.0)
            self.finished = True
            return

        remaining = self.speed * dt
        px, py, pz = self.position

        while remaining > 1e-6 and not self.finished:
            if self.segment_index >= len(self.path) - 1:
                self.finished = True
                self.velocity = (0.0, 0.0, 0.0)
                break

            tx, ty, tz = self.path[self.segment_index + 1]
            dx = tx - px
            dy = ty - py
            dz = tz - pz
            distance = math.sqrt(dx * dx + dy * dy + dz * dz)

            if distance < 1e-6:
                self.segment_index += 1
                px, py, pz = tx, ty, tz
                continue

            travel = min(distance, remaining)
            ratio = travel / distance
            px += dx * ratio
            py += dy * ratio
            pz += dz * ratio

            vx = dx / distance * self.speed
            vy = dy / distance * self.speed
            vz = dz / distance * self.speed
            self.velocity = (vx, vy, vz)

            remaining -= travel

            if abs(travel - distance) < 1e-6:
                self.segment_index += 1
                if self.segment_index >= len(self.path) - 1:
                    self.finished = True
                    px, py, pz = self.path[-1]
                    self.velocity = (0.0, 0.0, 0.0)

        self.position = (px, py, pz)


class MultiLevelEvacuationSimulator:
    """多楼层疏散仿真引擎，负责生成与推进跨层人员。"""

    def __init__(
        self,
        sim_settings: SimulationSettings,
        maps_dir,
    ):
        self.sim_settings = sim_settings
        self.maps_dir = maps_dir
        self.floor_grids: Dict[str, Grid] = {}
        self.path_planner = MultiLevelPathPlanner()
        self.agents: Dict[int, MultiLevelAgent] = {}
        self.paths_cache: Dict[int, List[WorldCoord]] = {}
        self.next_agent_id = 0
        self.blocked_by_floor: Dict[str, Set[GridCoord]] = {}
        self.cost_fields: Dict[str, Dict[GridCoord, float]] = {}
        self.active_spawn_floors: Optional[Set[str]] = None

        self.floor_exit_ids: Dict[str, List[str]] = {}
        self.target_floor: Optional[str] = None
        self.target_goal_ids: Optional[List[str]] = None

        self._initialize_floors()
        self._init_default_targets()

    def set_active_spawn_floors(self, floors: Optional[List[str]]) -> None:
        if floors:
            self.active_spawn_floors = {floor for floor in floors if floor in self.floor_grids}
        else:
            self.active_spawn_floors = None

    # ------------------------------------------------------------------
    # 初始化阶段
    # ------------------------------------------------------------------
    def _initialize_floors(self) -> None:
        if not self.sim_settings.floors:
            return

        for floor_id, floor_config in self.sim_settings.floors.items():
            grid = self._load_floor_grid(floor_config)
            self.floor_grids[floor_id] = grid

            exits_dict: Dict[str, List[GridCoord]] = {}
            for exit_cfg in floor_config.exits:
                rect = exit_cfg.get("rect")
                if not rect or len(rect) != 4:
                    continue
                x0, y0, w, h = rect
                coords: List[GridCoord] = []
                for dy in range(h):
                    for dx in range(w):
                        coords.append((x0 + dx, y0 + dy))
                exits_dict[exit_cfg["id"]] = coords

            exit_ids = list(exits_dict.keys())
            self.floor_exit_ids[floor_id] = exit_ids

            self.path_planner.add_floor(
                floor_id=floor_id,
                grid=grid,
                height=floor_config.height,
                exits=exits_dict,
            )

        if self.sim_settings.stairs:
            for stair_id, stair_cfg in self.sim_settings.stairs.items():
                self.path_planner.add_stair(stair_id, stair_cfg)

    def _load_floor_grid(self, floor_config: FloorConfig) -> Grid:
        map_path = self.maps_dir / floor_config.grid_file
        if not map_path.exists():
            map_path = self.maps_dir / self.sim_settings.map_name
        return load_grid(map_path)

    def _init_default_targets(self) -> None:
        if not self.floor_grids:
            self.target_floor = None
            self.target_goal_ids = None
            return
        if "floor1" in self.floor_grids:
            self.target_floor = "floor1"
            self.target_goal_ids = self.floor_exit_ids.get("floor1")
        else:
            self.target_floor = next(iter(self.floor_grids))
            self.target_goal_ids = self.floor_exit_ids.get(self.target_floor)

    def set_target_strategy(
        self,
        final_floor: Optional[str],
        goal_ids: Optional[List[str]],
    ) -> None:
        if final_floor and final_floor in self.floor_grids:
            self.target_floor = final_floor
        elif final_floor is not None:
            # 未知楼层则保持默认
            pass
        if goal_ids:
            self.target_goal_ids = goal_ids

    # ------------------------------------------------------------------
    # 人群初始化
    # ------------------------------------------------------------------
    def initialize_agents_multilevel(
        self,
        total_count: int,
        agent_config: AgentSpawnConfig,
        *,
        blocked_by_floor: Optional[Dict[str, Set[GridCoord]]] = None,
        cost_fields: Optional[Dict[str, Dict[GridCoord, float]]] = None,
    ) -> int:
        if not self.sim_settings.floors:
            return 0

        blocked_by_floor = blocked_by_floor or {}
        cost_fields = cost_fields or {}
        self.blocked_by_floor = blocked_by_floor
        self.cost_fields = cost_fields

        allocations = self._allocate_population(total_count)
        spawned = 0

        for floor_id, count in allocations.items():
            if count <= 0:
                continue
            grid = self.floor_grids[floor_id]
            floor_config = self.sim_settings.floors[floor_id]
            spawn_cells = self._sample_spawn_cells(
                grid,
                floor_config.spawn_regions,
                count,
                blocked=blocked_by_floor.get(floor_id),
            )

            for cell in spawn_cells:
                world_path = self._build_world_path(
                    start_floor=floor_id,
                    start_cell=cell,
                )
                if not world_path:
                    continue

                speed = _clamp(random.gauss(agent_config.speed_mean, agent_config.speed_std), 0.5, 3.5)
                agent = MultiLevelAgent(
                    id=self.next_agent_id,
                    path=world_path,
                    speed=speed,
                    position=world_path[0],
                )
                self.agents[agent.id] = agent
                self.paths_cache[agent.id] = world_path
                self.next_agent_id += 1
                spawned += 1

        return spawned

    def _allocate_population(self, total_count: int) -> Dict[str, int]:
        allocations: Dict[str, int] = {}
        if not self.sim_settings.floors:
            return allocations

        floordata = list(self.sim_settings.floors.items())
        allocated = 0
        remainders: List[Tuple[str, float]] = []
        active = self.active_spawn_floors

        ratio_denominator = 0.0
        if active:
            ratio_denominator = sum(cfg.agent_ratio for floor_id, cfg in floordata if floor_id in active)
            if ratio_denominator <= 0:
                ratio_denominator = float(len(active))

        for floor_id, cfg in floordata:
            if active and floor_id not in active:
                allocations[floor_id] = 0
                continue
            ratio = cfg.agent_ratio
            if active:
                ratio = (cfg.agent_ratio if ratio_denominator > 0 else 1.0) / ratio_denominator
            exact = total_count * ratio
            base = int(exact)
            allocations[floor_id] = base
            allocated += base
            remainders.append((floor_id, exact - base))

        remaining = total_count - allocated
        for floor_id, _ in sorted(remainders, key=lambda item: item[1], reverse=True):
            if active and floor_id not in active:
                continue
            if remaining <= 0:
                break
            allocations[floor_id] += 1
            remaining -= 1
        return allocations

    def _sample_spawn_cells(
        self,
        grid: Grid,
        spawn_regions: List[dict],
        count: int,
        *,
        blocked: Optional[Set[GridCoord]] = None,
    ) -> List[GridCoord]:
        blocked = blocked or set()
        candidates: List[GridCoord] = []

        for region in spawn_regions or []:
            rect = region.get("rect")
            if not rect or len(rect) != 4:
                continue
            x0, y0, w, h = rect
            for dy in range(h):
                for dx in range(w):
                    gx, gy = x0 + dx, y0 + dy
                    if 0 <= gx < grid.width and 0 <= gy < grid.height:
                        if (gx, gy) not in blocked and grid.cells[gy][gx].walkable:
                            candidates.append((gx, gy))

        if not candidates:
            for y in range(grid.height):
                for x in range(grid.width):
                    if (x, y) not in blocked and grid.cells[y][x].walkable:
                        candidates.append((x, y))

        if not candidates:
            return []

        if len(candidates) >= count:
            return random.sample(candidates, count)
        return [random.choice(candidates) for _ in range(count)]

    def _build_world_path(
        self,
        start_floor: str,
        start_cell: GridCoord,
    ) -> List[WorldCoord]:
        target_floor = self.target_floor or start_floor
        goal_ids = self.target_goal_ids or self.floor_exit_ids.get(target_floor, [])

        # 如果起点就是目标楼层且无指定目标，则只在本层寻找出口
        if start_floor == target_floor and not goal_ids:
            goal_ids = self.floor_exit_ids.get(start_floor, [])

        target_cells = self._get_exit_cells(target_floor, goal_ids)
        segments = self.path_planner.find_path(
            start_floor,
            start_cell,
            target_floor,
            target_cells,
            blocked_map=self.blocked_by_floor,
            cost_fields=self.cost_fields,
        )
        if not segments:
            return []
        return self.path_planner.add_stair_transitions(segments)

    def _get_exit_cells(self, floor_id: str, goal_ids: Optional[List[str]] = None) -> List[GridCoord]:
        cells: List[GridCoord] = []
        if goal_ids:
            for fid, grid in self.floor_grids.items():
                for goal in goal_ids:
                    if goal in grid.exits:
                        cells.extend(grid.exits[goal])
            if cells:
                return cells

        grid = self.floor_grids.get(floor_id)
        floor_config = self.sim_settings.floors.get(floor_id) if self.sim_settings.floors else None
        if floor_config and grid:
            for exit_cfg in floor_config.exits:
                exit_cells = grid.exits.get(exit_cfg["id"], [])
                cells.extend(exit_cells)
        if not cells and grid:
            cells.append((grid.width // 2, grid.height // 2))
        return cells

    # ------------------------------------------------------------------
    # 运行阶段
    # ------------------------------------------------------------------
    def agent_states(self) -> List[AgentState]:
        return [AgentState(id=agent.id, position=agent.position, velocity=agent.velocity) for agent in self.agents.values()]

    def paths(self) -> List[List[WorldCoord]]:
        return [path for path in self.paths_cache.values()]

    def tick(self, dt: float) -> None:
        finished: List[int] = []
        for agent in self.agents.values():
            agent.step(dt)
            if agent.finished:
                finished.append(agent.id)
        for agent_id in finished:
            self.agents.pop(agent_id, None)
            self.paths_cache.pop(agent_id, None)

    # ------------------------------------------------------------------
    # 重新规划
    # ------------------------------------------------------------------
    def update_navigation_fields(
        self,
        blocked_by_floor: Dict[str, Set[GridCoord]],
        cost_fields: Dict[str, Dict[GridCoord, float]],
        *,
        replan: bool = True,
        affected_floors: Optional[Set[str]] = None,
    ) -> None:
        self.blocked_by_floor = blocked_by_floor
        self.cost_fields = cost_fields
        if replan:
            self._replan_active_agents(affected_floors)

    def _replan_active_agents(self, affected_floors: Optional[Set[str]] = None) -> None:
        for agent in self.agents.values():
            floor_id = self._infer_floor_from_y(agent.position[1])
            if affected_floors and floor_id not in affected_floors:
                continue
            grid = self.floor_grids.get(floor_id)
            if grid is None:
                continue
            start_cell = self._world_to_cell(grid, agent.position)
            world_path = self._build_world_path(floor_id, start_cell)
            if not world_path:
                continue
            world_path[0] = agent.position
            agent.path = world_path
            agent.segment_index = 0
            agent.finished = False
            self.paths_cache[agent.id] = world_path

    def _infer_floor_from_y(self, y: float) -> str:
        if not self.sim_settings.floors:
            return "floor1"
        closest = None
        best_delta = float("inf")
        for floor_id, cfg in self.sim_settings.floors.items():
            delta = abs(cfg.height - y)
            if delta < best_delta:
                best_delta = delta
                closest = floor_id
        return closest or "floor1"

    def _world_to_cell(self, grid: Grid, position: WorldCoord) -> GridCoord:
        gx, gy = world_to_grid(position[0], position[2], grid.cell_size, grid.origin)
        gx = min(max(gx, 0), grid.width - 1)
        gy = min(max(gy, 0), grid.height - 1)
        return gx, gy
