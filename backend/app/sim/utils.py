"""仿真辅助函数与坐标转换工具。"""

from __future__ import annotations

from typing import Tuple


def grid_to_world(x: int, y: int, cell_size: float) -> Tuple[float, float, float]:
    """将网格坐标映射为 Three.js 使用的世界坐标 (x, y, z)。"""
    return (x * cell_size, 0.0, y * cell_size)


def world_to_grid(x: float, z: float, cell_size: float) -> Tuple[int, int]:
    """世界坐标 → 网格坐标。"""
    return int(round(x / cell_size)), int(round(z / cell_size))
