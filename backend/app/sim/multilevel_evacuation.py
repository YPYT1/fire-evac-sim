"""多楼层疏散仿真引擎：整合楼层地图、楼梯路径与跨层运动。"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..core.config import FloorConfig, SimulationSettings
from ..core.schemas import AgentSpawnConfig, AgentState, FireSource
from .grid import Grid, load_grid
from .multilevel import MultiLevelPathPlanner, PathSegment
from .utils import grid_to_world, world_to_grid

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
    exit_id: Optional[str] = None

    def step(self, dt: float, push: Optional[WorldCoord] = None) -> None:
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

        if push:
            px += push[0] * dt
            py += push[1] * dt
            pz += push[2] * dt
            vx, vy, vz = self.velocity
            self.velocity = (vx + push[0], vy + push[1], vz + push[2])

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
        self.fires_by_floor: Dict[str, List[FireSource]] = {}
        self.exit_load: Dict[str, int] = {}
        self.agent_targets: Dict[int, str] = {}
        self.route_rng = random.Random()
        self.exit_congestion_weight = 0.8
        self.exit_fire_block_radius = 3.5
        self.fire_avoid_distance = 4.0
        self.exit_fire_penalty_weight = 6.0
        self.path_jitter_strength = 0.6
        self.route_noise = 4.0
        self.repulsion_radius = 1.3
        self.repulsion_gain = 1.2
        self.repulsion_push_strength = 0.5

        self.floor_exit_ids: Dict[str, List[str]] = {}
        self.target_floor: Optional[str] = None
        self.target_goal_ids: Optional[List[str]] = None

        self._initialize_floors()
        self._init_default_targets()
        self._apply_crowd_overrides()

    def _apply_crowd_overrides(self) -> None:
        crowd = getattr(self.sim_settings, "crowd", None)
        if not crowd:
            return
        if crowd.repulsion_radius > 0:
            self.repulsion_radius = crowd.repulsion_radius
        self.repulsion_gain = crowd.repulsion_gain
        self.repulsion_push_strength = crowd.repulsion_push_strength

    def set_active_spawn_floors(self, floors: Optional[List[str]]) -> None:
        if floors:
            self.active_spawn_floors = {floor for floor in floors if floor in self.floor_grids}
        else:
            self.active_spawn_floors = None

    def set_floor_fires(self, floor_fires: Optional[Dict[str, List[FireSource]]]) -> None:
        if not floor_fires:
            self.fires_by_floor = {}
            return
        self.fires_by_floor = {floor_id: list(fires) for floor_id, fires in floor_fires.items()}

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
        floor_fires: Optional[Dict[str, List[FireSource]]] = None,
    ) -> int:
        if not self.sim_settings.floors:
            return 0

        if floor_fires is not None:
            self.set_floor_fires(floor_fires)

        blocked_by_floor = blocked_by_floor or {}
        cost_fields = cost_fields or {}
        self.blocked_by_floor = blocked_by_floor
        self.cost_fields = cost_fields
        self.agents.clear()
        self.paths_cache.clear()
        self.agent_targets.clear()
        self._init_exit_loads()
        self.next_agent_id = 0

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
                world_path, exit_id = self._plan_route(
                    start_floor=floor_id,
                    start_cell=cell,
                )
                if not world_path or not exit_id:
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
                self._assign_exit_id(agent, exit_id)
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

    def _init_exit_loads(self) -> None:
        self.exit_load = {}
        for exit_ids in self.floor_exit_ids.values():
            for exit_id in exit_ids:
                self.exit_load.setdefault(exit_id, 0)

    def _assign_exit_id(self, agent: MultiLevelAgent, exit_id: Optional[str]) -> None:
        if agent.exit_id:
            prev = agent.exit_id
            self.exit_load[prev] = max(0, self.exit_load.get(prev, 0) - 1)
            self.agent_targets.pop(agent.id, None)
        agent.exit_id = exit_id
        if exit_id:
            self.exit_load[exit_id] = self.exit_load.get(exit_id, 0) + 1
            self.agent_targets[agent.id] = exit_id

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

    def _plan_route(
        self,
        start_floor: str,
        start_cell: GridCoord,
    ) -> Tuple[List[WorldCoord], Optional[str]]:
        target_floor = self.target_floor or start_floor
        goal_ids = self.target_goal_ids or self.floor_exit_ids.get(target_floor, [])

        if start_floor == target_floor and not goal_ids:
            goal_ids = self.floor_exit_ids.get(start_floor, [])

        selection = self._select_exit_route(
            start_floor=start_floor,
            start_cell=start_cell,
            target_floor=target_floor,
            goal_ids=goal_ids,
        )
        if not selection:
            return [], None

        exit_id, base_path, floor_tags = selection
        varied_path = self._apply_path_variation(base_path, floor_tags)
        return varied_path, exit_id

    def _select_exit_route(
        self,
        start_floor: str,
        start_cell: GridCoord,
        target_floor: str,
        goal_ids: Optional[List[str]],
    ) -> Optional[Tuple[str, List[WorldCoord], List[str]]]:
        candidate_exit_ids = list(goal_ids or [])
        if not candidate_exit_ids:
            candidate_exit_ids = list(self.floor_exit_ids.get(target_floor, []))
        if not candidate_exit_ids:
            candidate_exit_ids = list(self.floor_exit_ids.get(start_floor, []))
        if not candidate_exit_ids:
            return None

        self.route_rng.shuffle(candidate_exit_ids)
        safe_candidates: List[Tuple[float, str, List[WorldCoord], List[str]]] = []
        unsafe_candidates: List[Tuple[float, str, List[WorldCoord], List[str]]] = []

        for exit_id in candidate_exit_ids:
            target_cells = self._get_exit_cells_for_id(target_floor, exit_id)
            if not target_cells:
                continue
            segments = self.path_planner.find_path(
                start_floor,
                start_cell,
                target_floor,
                target_cells,
                blocked_map=self.blocked_by_floor,
                cost_fields=self.cost_fields,
            )
            if not segments:
                continue
            world_path, floor_tags = self._compose_world_path(segments)
            if len(world_path) < 2:
                continue

            base_length = self._path_length(world_path)
            exit_penalty, blocked = self._exit_fire_penalty(target_floor, exit_id)
            path_penalty = self._path_fire_penalty(world_path, floor_tags)
            congestion_penalty = self.exit_congestion_weight * float(self.exit_load.get(exit_id, 0))
            randomness = self.route_rng.uniform(0.0, self.route_noise)
            score = base_length + exit_penalty + path_penalty + congestion_penalty + randomness
            candidate = (score, exit_id, world_path, floor_tags)
            if blocked:
                unsafe_candidates.append(candidate)
            else:
                safe_candidates.append(candidate)

        if safe_candidates:
            safe_candidates.sort(key=lambda item: item[0])
            _, exit_id, path, tags = safe_candidates[0]
            return exit_id, path, tags
        if unsafe_candidates:
            unsafe_candidates.sort(key=lambda item: item[0])
            _, exit_id, path, tags = unsafe_candidates[0]
            return exit_id, path, tags
        return None

    def _compose_world_path(self, segments: List[PathSegment]) -> Tuple[List[WorldCoord], List[str]]:
        points: List[WorldCoord] = []
        floor_tags: List[str] = []
        for index, segment in enumerate(segments):
            if not segment.world_path:
                continue
            for coord in segment.world_path:
                points.append(coord)
                floor_tags.append(segment.floor_id)
            if index < len(segments) - 1:
                next_segment = segments[index + 1]
                if not next_segment.world_path:
                    continue
                last_point = segment.world_path[-1]
                next_point = next_segment.world_path[0]
                if last_point != next_point:
                    mid_y = (last_point[1] + next_point[1]) * 0.5
                    points.append((last_point[0], mid_y, last_point[2]))
                    floor_tags.append("stair")

        deduped_points: List[WorldCoord] = []
        deduped_tags: List[str] = []
        for idx, coord in enumerate(points):
            if idx > 0 and coord == points[idx - 1]:
                continue
            deduped_points.append(coord)
            deduped_tags.append(floor_tags[idx])
        return deduped_points, deduped_tags

    def _apply_path_variation(self, path: List[WorldCoord], floor_tags: List[str]) -> List[WorldCoord]:
        if len(path) < 3 or not self.path_jitter_strength:
            return path

        varied: List[WorldCoord] = [path[0]]
        for idx in range(1, len(path) - 1):
            tag = floor_tags[idx] if idx < len(floor_tags) else None
            if tag == "stair":
                varied.append(path[idx])
                continue
            prev_point = path[idx - 1]
            curr_point = path[idx]
            next_point = path[idx + 1]
            dir_x = next_point[0] - prev_point[0]
            dir_z = next_point[2] - prev_point[2]
            length = math.hypot(dir_x, dir_z)
            if length < 1e-3:
                varied.append(curr_point)
                continue
            normal_x = -dir_z / length
            normal_z = dir_x / length
            strength = self.path_jitter_strength * self.route_rng.uniform(-1.0, 1.0)
            candidate = (
                curr_point[0] + normal_x * strength,
                curr_point[1],
                curr_point[2] + normal_z * strength,
            )
            if tag and not self._is_walkable_point(candidate, tag):
                varied.append(curr_point)
            else:
                varied.append(candidate)

        varied.append(path[-1])
        return varied

    def _get_exit_cells_for_id(self, floor_id: str, exit_id: str) -> List[GridCoord]:
        grid = self.floor_grids.get(floor_id)
        if not grid:
            return []
        return list(grid.exits.get(exit_id, []))

    def _exit_fire_penalty(self, floor_id: str, exit_id: str) -> Tuple[float, bool]:
        fires = self.fires_by_floor.get(floor_id) or []
        if not fires:
            return 0.0, False
        centroid = self._exit_centroid(floor_id, exit_id)
        if centroid is None:
            return 0.0, False
        min_distance = min(
            math.hypot(centroid[0] - fire.position[0], centroid[2] - fire.position[2])
            for fire in fires
        )
        if min_distance < self.exit_fire_block_radius:
            return self.exit_fire_penalty_weight * 10.0, True
        return self.exit_fire_penalty_weight / max(min_distance, 0.5), False

    def _path_fire_penalty(self, path: List[WorldCoord], floor_tags: List[str]) -> float:
        penalty = 0.0
        for point, tag in zip(path, floor_tags):
            if tag == "stair":
                continue
            fires = self.fires_by_floor.get(tag) or []
            if not fires:
                continue
            min_distance = min(
                math.hypot(point[0] - fire.position[0], point[2] - fire.position[2])
                for fire in fires
            )
            if min_distance < self.fire_avoid_distance:
                penalty += (self.fire_avoid_distance - min_distance)
        return penalty

    def _exit_centroid(self, floor_id: str, exit_id: str) -> Optional[WorldCoord]:
        grid = self.floor_grids.get(floor_id)
        if not grid:
            return None
        cells = grid.exits.get(exit_id, [])
        if not cells:
            return None
        sx = 0.0
        sz = 0.0
        for cx, cy in cells:
            wx, _, wz = grid_to_world(cx, cy, grid.cell_size, grid.origin)
            sx += wx
            sz += wz
        count = len(cells)
        return (sx / count, grid.origin[1], sz / count)

    def _path_length(self, path: List[WorldCoord]) -> float:
        if len(path) < 2:
            return 0.0
        length = 0.0
        for idx in range(len(path) - 1):
            ax, ay, az = path[idx]
            bx, by, bz = path[idx + 1]
            length += math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)
        return length

    def _is_walkable_point(self, point: WorldCoord, floor_id: str) -> bool:
        grid = self.floor_grids.get(floor_id)
        if not grid:
            return True
        gx, gy = world_to_grid(point[0], point[2], grid.cell_size, grid.origin)
        if not (0 <= gx < grid.width and 0 <= gy < grid.height):
            return False
        cell = grid.cells[gy][gx]
        if not cell.walkable:
            return False
        blocked = self.blocked_by_floor.get(floor_id)
        if blocked and (gx, gy) in blocked:
            return False
        return True

    # ------------------------------------------------------------------
    # 运行阶段
    # ------------------------------------------------------------------
    def agent_states(self) -> List[AgentState]:
        return [AgentState(id=agent.id, position=agent.position, velocity=agent.velocity) for agent in self.agents.values()]

    def paths(self) -> List[List[WorldCoord]]:
        return [path for path in self.paths_cache.values()]

    def tick(self, dt: float) -> None:
        finished: List[int] = []
        repulsions = self._compute_repulsions()
        for agent in self.agents.values():
            agent.step(dt, repulsions.get(agent.id))
            if agent.finished:
                finished.append(agent.id)
        for agent_id in finished:
            agent = self.agents.pop(agent_id, None)
            if agent is not None:
                self._assign_exit_id(agent, None)
            self.paths_cache.pop(agent_id, None)

    # ------------------------------------------------------------------
    # 重新规划
    # ------------------------------------------------------------------
    def update_navigation_fields(
        self,
        blocked_by_floor: Dict[str, Set[GridCoord]],
        cost_fields: Dict[str, Dict[GridCoord, float]],
        *,
        floor_fires: Optional[Dict[str, List[FireSource]]] = None,
        replan: bool = True,
        affected_floors: Optional[Set[str]] = None,
    ) -> None:
        self.blocked_by_floor = blocked_by_floor
        self.cost_fields = cost_fields
        if floor_fires is not None:
            self.set_floor_fires(floor_fires)
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
            world_path, exit_id = self._plan_route(floor_id, start_cell)
            if not world_path:
                continue
            world_path[0] = agent.position
            agent.path = world_path
            agent.segment_index = 0
            agent.finished = False
            self.paths_cache[agent.id] = world_path
            if exit_id:
                self._assign_exit_id(agent, exit_id)

    def _compute_repulsions(self) -> Dict[int, WorldCoord]:
        if not self.agents:
            return {}
        pushes: Dict[int, WorldCoord] = {}
        floor_groups: Dict[str, List[MultiLevelAgent]] = defaultdict(list)
        for agent in self.agents.values():
            floor_id = self._infer_floor_from_y(agent.position[1])
            floor_groups[floor_id].append(agent)

        for floor_id, group in floor_groups.items():
            if len(group) < 2:
                continue
            for agent in group:
                push_x = 0.0
                push_z = 0.0
                for neighbor in group:
                    if neighbor.id == agent.id:
                        continue
                    dx = agent.position[0] - neighbor.position[0]
                    dz = agent.position[2] - neighbor.position[2]
                    dist = math.hypot(dx, dz)
                    if dist < 1e-3 or dist > self.repulsion_radius:
                        continue
                    strength = (self.repulsion_radius - dist) / self.repulsion_radius
                    scale = strength * self.repulsion_gain
                    push_x += (dx / dist) * scale
                    push_z += (dz / dist) * scale
                if abs(push_x) < 1e-4 and abs(push_z) < 1e-4:
                    continue
                candidate = (
                    agent.position[0] + push_x * 0.5,
                    agent.position[1],
                    agent.position[2] + push_z * 0.5,
                )
                if not self._is_walkable_point(candidate, floor_id):
                    continue
                pushes[agent.id] = (
                    push_x * self.repulsion_push_strength,
                    0.0,
                    push_z * self.repulsion_push_strength,
                )
        return pushes

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
