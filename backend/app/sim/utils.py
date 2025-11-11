"""仿真辅助函数与坐标转换工具。"""

from __future__ import annotations

import random
from typing import Iterable, List, Sequence, Tuple


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


def scatter_cells(
    candidates: Sequence[Tuple[int, int]] | Iterable[Tuple[int, int]],
    count: int,
    min_distance: int,
    rng: random.Random,
) -> List[Tuple[int, int]]:
    """在候选单元中进行离散抽样，尽量保证点位覆盖范围分散。"""

    if count <= 0:
        return []

    if not isinstance(candidates, list):
        pool = list(candidates)
    else:
        pool = candidates.copy()

    if not pool:
        return []

    min_distance = max(1, int(min_distance or 0))
    sample_quota = min(count, len(pool))
    rng.shuffle(pool)

    if min_distance <= 1:
        picked = list(pool[:sample_quota])
    else:
        picked = []
        bucket_size = min_distance
        buckets: dict[tuple[int, int], list[Tuple[int, int]]] = {}

        for cell in pool:
            bx = cell[0] // bucket_size
            by = cell[1] // bucket_size
            ok = True
            for nx in range(bx - 1, bx + 2):
                for ny in range(by - 1, by + 2):
                    for ox, oy in buckets.get((nx, ny), []):
                        if abs(cell[0] - ox) + abs(cell[1] - oy) < min_distance:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if ok:
                picked.append(cell)
                buckets.setdefault((bx, by), []).append(cell)
            if len(picked) >= sample_quota:
                break

        if len(picked) < sample_quota:
            remaining = [cell for cell in pool if cell not in picked]
            if remaining:
                needed = min(sample_quota - len(picked), len(remaining))
                picked.extend(remaining[:needed])

    # 若仍未满足需求，允许放宽约束进行补齐（可重复）
    while len(picked) < count:
        choice = rng.choice(picked or pool)
        picked.append(choice)

    return picked[:count]
