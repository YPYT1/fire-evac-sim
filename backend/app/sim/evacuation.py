"""基于栅格的简易疏散仿真：负责生成路径并推进代理位置。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..core.schemas import AgentSpawnConfig, AgentState
from .grid import Grid
from .planner import astar
from .utils import grid_to_world

GridCoord = Tuple[int, int]
WorldCoord = Tuple[float, float, float]


@dataclass
class AgentTrack:
  """维护单个代理的路径与运动状态。"""

  id: int
  path_grid: List[GridCoord]
  path_world: List[WorldCoord]
  speed: float
  position: WorldCoord
  velocity: WorldCoord = (0.0, 0.0, 0.0)
  segment_index: int = 0
  finished: bool = False

  def step(self, dt: float) -> None:
    """沿路径前进。"""

    if self.finished:
      self.velocity = (0.0, 0.0, 0.0)
      return

    if len(self.path_world) < 2:
      self.finished = True
      self.velocity = (0.0, 0.0, 0.0)
      return

    remaining = self.speed * dt
    px, py, pz = self.position

    while remaining > 1e-6 and not self.finished:
      if self.segment_index >= len(self.path_world) - 1:
        self.finished = True
        self.velocity = (0.0, 0.0, 0.0)
        break

      tx, ty, tz = self.path_world[self.segment_index + 1]
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
        if self.segment_index >= len(self.path_world) - 1:
          self.finished = True
          px, py, pz = self.path_world[-1]
          self.velocity = (0.0, 0.0, 0.0)

    self.position = (px, py, pz)


def _expand_rect(rect: Sequence[int]) -> List[GridCoord]:
  if len(rect) != 4:
    return []
  x0, y0, w, h = rect
  coords: List[GridCoord] = []
  for dy in range(h):
    for dx in range(w):
      coords.append((x0 + dx, y0 + dy))
  return coords


class EvacuationSimulator:
  """负责路径规划、代理生成与逐帧推进。"""

  def __init__(self, grid: Grid, rng: random.Random | None = None) -> None:
    self.grid = grid
    self.rng = rng or random.Random()
    self.tracks: List[AgentTrack] = []
    self.paths_for_visual: Dict[int, List[WorldCoord]] = {}

  def initialize_agents(
    self,
    agent_cfg: AgentSpawnConfig,
    start_regions: Iterable[dict],
    goal_ids: Sequence[str] | None = None,
    floor_y: float = 0.0,
    *,
    blocked: Optional[set[GridCoord]] = None,
    cost_field: Optional[Dict[GridCoord, float]] = None,
    override_start: Optional[Sequence[GridCoord]] = None,
  ) -> int:
    """按照配置生成代理并计算路径。返回成功生成数量。"""

    goals = list(goal_ids or [])
    if not goals:
      goals = list(self.grid.exits.keys())
    exits = {goal: self.grid.exits.get(goal, []) for goal in goals}
    exits = {k: v for k, v in exits.items() if v}
    if not exits:
      return 0

    blocked_set = set(blocked or [])
    candidates: List[GridCoord] = []
    if override_start:
      candidates.extend(list(override_start))
    else:
      for region in start_regions:
        rect = region.get("rect")
        if not rect:
          continue
        for cell in _expand_rect(rect):
          x, y = cell
          if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
            if self.grid.cells[y][x].walkable:
              candidates.append(cell)
    if not candidates:
      # fallback：使用全局可行单元
      for y in range(self.grid.height):
        for x in range(self.grid.width):
          if self.grid.cells[y][x].walkable:
            candidates.append((x, y))

    if blocked_set:
      candidates = [cell for cell in candidates if cell not in blocked_set]

    if not candidates:
      # 若所有候选都与火源冲突，则再次遍历全局找可用点
      for y in range(self.grid.height):
        for x in range(self.grid.width):
          if self.grid.cells[y][x].walkable and (x, y) not in blocked_set:
            candidates.append((x, y))

    if not candidates:
      return 0

    self.rng.shuffle(candidates)

    spawned = 0
    self.tracks.clear()
    self.paths_for_visual.clear()

    for agent_id in range(agent_cfg.count):
      start = self.rng.choice(candidates)
      exit_id = self.rng.choice(list(exits.keys()))
      target_cells = exits[exit_id]

      active_blocked = set(blocked or [])
      active_blocked.discard(start)
      path_grid = self._compute_path(start, target_cells, blocked=active_blocked, cost_field=cost_field)
      if not path_grid:
        continue

      origin_override = (self.grid.origin[0], floor_y, self.grid.origin[2])
      base_path = [grid_to_world(x, y, self.grid.cell_size, origin_override) for x, y in path_grid]
      if floor_y > 0 and base_path:
        top = base_path[0]
        mid = (top[0], max(floor_y * 0.5, 0.5), top[2])
        bottom = (top[0], 0.0, top[2])
        remainder = [(px, 0.0, pz) for px, _, pz in base_path[1:]]
        path_world = [top, mid, bottom, *remainder]
      else:
        path_world = base_path

      speed = max(0.5, self.rng.normalvariate(agent_cfg.speed_mean, agent_cfg.speed_std))
      track = AgentTrack(
        id=agent_id,
        path_grid=path_grid,
        path_world=path_world,
        speed=speed,
        position=path_world[0],
      )
      self.tracks.append(track)
      self.paths_for_visual[agent_id] = path_world
      spawned += 1

    return spawned

  def step(self, dt: float) -> None:
    """前进一步。"""

    survivors: List[AgentTrack] = []
    for track in self.tracks:
      track.step(dt)
      if not track.finished:
        survivors.append(track)
    self.tracks = survivors

  def agent_states(self) -> List[AgentState]:
    """导出当前代理状态。"""

    return [
      AgentState(id=track.id, position=track.position, velocity=track.velocity)
      for track in self.tracks
    ]

  def paths(self) -> List[List[WorldCoord]]:
    """返回用于可视化的全部路径。"""

    return list(self.paths_for_visual.values())

  def remaining_agents(self) -> int:
    return len(self.tracks)

  def _compute_path(
    self,
    start: GridCoord,
    goal_cells: Sequence[GridCoord],
    *,
    blocked: Optional[set[GridCoord]] = None,
    cost_field: Optional[Dict[GridCoord, float]] = None,
  ) -> List[GridCoord]:
    """从起点到目标单元集合中距离最短的路径。"""

    best_path: List[GridCoord] = []
    best_length = math.inf

    for goal in goal_cells:
      path = astar(self.grid, start, goal, blocked=blocked, cost_field=cost_field)
      if path and len(path) < best_length:
        best_path = path
        best_length = len(path)
    return best_path
