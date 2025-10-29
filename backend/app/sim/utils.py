"""仿真辅助函数与坐标转换工具。"""

from __future__ import annotations

from typing import Tuple


def grid_to_world(
    x: float,
    y: float,
    cell_size: float,
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    center: bool = True,
) -> Tuple[float, float, float]:
    """将网格坐标映射为世界坐标 (x, y, z)。

    参数 center=True 时返回单元中心，False 则返回单元原点。
    """

    offset = 0.5 if center else 0.0
    ox, oy, oz = origin
    return (ox + (x + offset) * cell_size, oy, oz + (y + offset) * cell_size)


def world_to_grid(
    x: float,
    z: float,
    cell_size: float,
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> Tuple[int, int]:
    """世界坐标 → 网格坐标（四舍五入到最近的单元中心）。"""

    ox, _, oz = origin
    gx = int(round((x - ox) / cell_size - 0.5))
    gy = int(round((z - oz) / cell_size - 0.5))
    return gx, gy
