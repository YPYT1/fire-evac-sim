"""火源建模与代价场计算。"""

from __future__ import annotations

import random
from typing import Iterable, List, Sequence

import numpy as np

from ..core.schemas import FireSource
from .grid import Grid


def build_cost_field(grid: Grid, fires: Iterable[FireSource], decay: float = 0.95) -> np.ndarray:
    """根据火源生成代价场，占位实现使用简单的指数衰减模型。"""

    cost = np.ones((grid.height, grid.width), dtype=np.float32)
    for fire in fires:
        fx, _, fy = fire.position
        gx, gy = int(round(fx / grid.cell_size)), int(round(fy / grid.cell_size))
        if not (0 <= gx < grid.width and 0 <= gy < grid.height):
            continue
        for y in range(grid.height):
            for x in range(grid.width):
                distance = abs(x - gx) + abs(y - gy)
                cost[y, x] += fire.intensity * (decay ** distance)
    return cost


def sample_random_fire_positions(
    grid: Grid,
    count: int,
    *,
    floor_y: float = 0.0,
    intensity_range: Sequence[float] = (0.8, 1.2),
    rng: random.Random | None = None,
) -> List[FireSource]:
    """从全局可行走区域随机生成指定数量的火源。"""

    rng = rng or random.Random()
    walkable: List[tuple[int, int]] = []
    for y in range(grid.height):
        for x in range(grid.width):
            if grid.cells[y][x].walkable:
                walkable.append((x, y))

    if not walkable or count <= 0:
        return []

    min_intensity = float(intensity_range[0]) if len(intensity_range) >= 1 else 0.8
    max_intensity = float(intensity_range[1]) if len(intensity_range) >= 2 else min_intensity
    if max_intensity < min_intensity:
        min_intensity, max_intensity = max_intensity, min_intensity

    unique_count = min(count, len(walkable))
    selected = rng.sample(walkable, unique_count)
    while len(selected) < count:
        selected.append(rng.choice(walkable))

    fires: List[FireSource] = []
    for x, y in selected:
        intensity = rng.uniform(min_intensity, max_intensity)
        fires.append(
            FireSource(
                position=(x * grid.cell_size, floor_y, y * grid.cell_size),
                intensity=float(intensity),
            )
        )
    return fires
