"""火源代价场生成测试。"""

import numpy as np

from backend.app.sim.fire import build_cost_field
from backend.app.sim.grid import Grid, GridCell
from backend.app.core.schemas import FireSource


def test_build_cost_field_increases_near_fire():
    cells = [[GridCell(True) for _ in range(3)] for _ in range(3)]
    grid = Grid(width=3, height=3, cell_size=1.0, cells=cells)
    fire = FireSource(position=(1.0, 0.0, 1.0), intensity=1.0)

    cost = build_cost_field(grid, [fire])

    center_cost = cost[1, 1]
    corner_cost = cost[0, 0]
    assert isinstance(cost, np.ndarray)
    assert center_cost > corner_cost
