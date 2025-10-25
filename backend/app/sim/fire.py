"""火源建模与代价场计算。"""

from __future__ import annotations

from typing import Iterable, List

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


def sample_random_fire_positions(grid: Grid, count: int) -> List[FireSource]:
    """随机抽样火源位置，占位实现将从可行走区域均匀选择。"""

    fires: List[FireSource] = []
    step = max(1, (grid.width * grid.height) // max(count, 1))
    idx = 0
    for y in range(grid.height):
        for x in range(grid.width):
            cell = grid.cells[y][x]
            if not cell.walkable:
                continue
            if idx % step == 0 and len(fires) < count:
                fires.append(
                    FireSource(
                        position=(x * grid.cell_size, 0.0, y * grid.cell_size),
                        intensity=1.0,
                    )
                )
            idx += 1
    return fires
