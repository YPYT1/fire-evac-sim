"""A* 路径规划基础测试。"""

from backend.app.sim.grid import Grid, GridCell
from backend.app.sim.planner import astar


def _make_open_grid(size: int = 3) -> Grid:
    cells = [[GridCell(True) for _ in range(size)] for _ in range(size)]
    return Grid(width=size, height=size, cell_size=1.0, cells=cells)


def test_astar_finds_goal():
    grid = _make_open_grid(3)
    path = astar(grid, (0, 0), (2, 2))
    assert path[0] == (0, 0)
    assert path[-1] == (2, 2)
    assert len(path) >= 5  # 直角路径至少包含 5 个节点


def test_astar_handles_blocked_neighbors():
    grid = _make_open_grid(3)
    # 阻塞中心节点，确保算法绕行
    grid.cells[1][1].walkable = False

    path = astar(grid, (0, 0), (2, 2))
    assert (1, 1) not in path  # 中心节点被阻塞
    assert path[-1] == (2, 2)
