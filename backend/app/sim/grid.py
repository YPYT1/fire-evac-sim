"""地图栅格与几何相关的工具方法。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List


@dataclass
class GridCell:
    """栅格单元的占位表示。"""

    walkable: bool
    cost: float = 1.0


@dataclass
class Grid:
    """简易栅格结构，可在后续替换更高效的数据结构。"""

    width: int
    height: int
    cell_size: float
    cells: List[List[GridCell]]

    def neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """返回可行走邻居。"""
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        result: list[tuple[int, int]] = []
        for dx, dy in offsets:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                cell = self.cells[ny][nx]
                if cell.walkable:
                    result.append((nx, ny))
        return result


def load_grid(path: Path) -> Grid:
    """从 JSON 文件加载占位网格数据。"""
    payload = json.loads(path.read_text(encoding="utf-8"))
    width = payload["width"]
    height = payload["height"]
    cell_size = payload.get("cellSize", 1.0)
    raw_cells: list[list[Any]] = payload["cells"]

    cells = [
        [GridCell(walkable=cell["walkable"], cost=cell.get("cost", 1.0)) for cell in row]
        for row in raw_cells
    ]

    return Grid(width=width, height=height, cell_size=cell_size, cells=cells)
