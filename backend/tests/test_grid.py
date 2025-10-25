"""网格加载与邻接逻辑测试。"""

from pathlib import Path

from backend.app.sim.grid import Grid, GridCell, load_grid


def test_load_grid_from_demo_map():
    path = Path("backend/app/data/maps/demo_map.json")
    grid = load_grid(path)
    assert grid.width == 10
    assert grid.height == 10
    assert grid.cell_size == 1.0
    assert all(cell.walkable for row in grid.cells for cell in row)


def test_neighbors_returns_valid_indices():
    cells = [[GridCell(True) for _ in range(3)] for _ in range(3)]
    grid = Grid(width=3, height=3, cell_size=1.0, cells=cells)

    neighbors = grid.neighbors(1, 1)
    assert set(neighbors) == {(0, 1), (2, 1), (1, 0), (1, 2)}
