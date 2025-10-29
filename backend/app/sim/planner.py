"""路径规划占位实现：首版使用 A*。"""

from __future__ import annotations

import heapq
from typing import Dict, Iterable, List, Optional, Tuple

from .grid import Grid

Coordinate = Tuple[int, int]


def heuristic(a: Coordinate, b: Coordinate) -> float:
    """曼哈顿距离启发函数。"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct_path(came_from: Dict[Coordinate, Coordinate], current: Coordinate) -> List[Coordinate]:
    """回溯坐标路径。"""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def astar(
    grid: Grid,
    start: Coordinate,
    goal: Coordinate,
    *,
    blocked: Optional[Iterable[Coordinate]] = None,
    cost_field: Optional[Dict[Coordinate, float]] = None,
) -> List[Coordinate]:
    """简易 A* 实现，支持动态禁行与代价场。"""

    open_set: list[tuple[float, Coordinate]] = []
    heapq.heappush(open_set, (0.0, start))

    came_from: Dict[Coordinate, Coordinate] = {}
    g_score: Dict[Coordinate, float] = {start: 0.0}
    blocked_set = set(blocked or [])

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in grid.neighbors(*current):
            if neighbor in blocked_set:
                continue
            tentative_g = g_score[current] + 1.0
            if cost_field:
                tentative_g += float(cost_field.get(neighbor, 0.0))
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return []
