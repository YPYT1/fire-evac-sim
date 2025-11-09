"""多楼层路径规划模块：支持跨楼层路径计算和楼梯导航。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..core.config import StairConfig
from .grid import Grid
from .planner import astar

GridCoord = Tuple[int, int]
WorldCoord = Tuple[float, float, float]


@dataclass
class FloorNode:
    """楼层节点，表示路径规划中的一个楼层"""
    floor_id: str
    grid: Grid
    height: float
    exits: Dict[str, List[GridCoord]]  # 出口ID -> 单元格列表
    stairs_down: Dict[str, List[GridCoord]]  # 下楼楼梯ID -> 单元格列表
    stairs_up: Dict[str, List[GridCoord]]  # 上楼楼梯ID -> 单元格列表


@dataclass
class PathSegment:
    """路径段，表示单层内的路径"""
    floor_id: str
    floor_height: float
    grid_path: List[GridCoord]
    world_path: List[WorldCoord]
    segment_type: str  # 'walk', 'stair_down', 'stair_up'


class MultiLevelPathPlanner:
    """多楼层路径规划器"""
    
    def __init__(self):
        self.floors: Dict[str, FloorNode] = {}
        self.stair_connections: Dict[str, List[Tuple[str, str, List[GridCoord], List[GridCoord]]]] = {}
        # stair_id -> [(from_floor, to_floor, entry_cells, exit_cells), ...]
        
    def add_floor(
        self,
        floor_id: str,
        grid: Grid,
        height: float,
        exits: Dict[str, List[GridCoord]],
    ) -> None:
        """添加楼层节点"""
        self.floors[floor_id] = FloorNode(
            floor_id=floor_id,
            grid=grid,
            height=height,
            exits=exits,
            stairs_down={},
            stairs_up={},
        )
    
    def add_stair(
        self,
        stair_id: str,
        stair_config: StairConfig,
    ) -> None:
        """添加楼梯连接"""
        connections = []
        for conn in stair_config.connections:
            from_floor = conn.from_floor
            to_floor = conn.to_floor
            entry_cells = [tuple(cell) for cell in conn.entry_cells]
            exit_cells = [tuple(cell) for cell in conn.exit_cells]
            connections.append((from_floor, to_floor, entry_cells, exit_cells))
            
            # 更新楼层的楼梯信息
            if from_floor in self.floors:
                self.floors[from_floor].stairs_down.setdefault(stair_id, entry_cells)
            if to_floor in self.floors:
                self.floors[to_floor].stairs_up.setdefault(stair_id, exit_cells)
        
        self.stair_connections[stair_id] = connections
    
    def find_path(
        self,
        start_floor: str,
        start_cell: GridCoord,
        target_floor: str,
        target_cells: List[GridCoord],
        *,
        blocked_map: Optional[Dict[str, Set[GridCoord]]] = None,
        cost_fields: Optional[Dict[str, Dict[GridCoord, float]]] = None,
    ) -> List[PathSegment]:
        """
        查找从起点楼层到目标楼层的完整路径。
        
        如果起点和目标在同一楼层，直接计算单层路径。
        如果需要跨楼层，计算多段路径：当前层 -> 楼梯 -> 下层 -> ... -> 目标层
        """
        blocked_map = blocked_map or {}
        cost_fields = cost_fields or {}

        if start_floor == target_floor:
            # 同楼层路径
            return self._compute_single_floor_path(
                start_floor,
                start_cell,
                target_cells,
                blocked=blocked_map.get(start_floor),
                cost_field=cost_fields.get(start_floor),
            )
        
        # 跨楼层路径：需要找到楼梯序列
        floor_sequence = self._find_floor_sequence(start_floor, target_floor)
        if not floor_sequence:
            return []
        
        segments: List[PathSegment] = []
        current_cell = start_cell
        
        for i in range(len(floor_sequence) - 1):
            current_floor_id = floor_sequence[i]
            next_floor_id = floor_sequence[i + 1]
            
            candidates = self._stairs_between_floors(current_floor_id, next_floor_id)
            if not candidates:
                return []
            
            best_option = None
            best_length = math.inf
            floor_node = self.floors[current_floor_id]
            blocked = blocked_map.get(current_floor_id)
            cost_field = cost_fields.get(current_floor_id)
            
            for entry_cells, exit_cells in candidates:
                path_to_stair = self._compute_path_to_cells(
                    floor_node,
                    current_cell,
                    entry_cells,
                    blocked=blocked,
                    cost_field=cost_field,
                )
                if not path_to_stair:
                    continue
                if len(path_to_stair) < best_length:
                    best_length = len(path_to_stair)
                    best_option = (path_to_stair, exit_cells)
            
            if not best_option:
                return []
            
            path_to_stair, exit_cells = best_option
            
            segment = self._create_path_segment(
                current_floor_id,
                floor_node.height,
                floor_node.grid,
                path_to_stair,
                'walk',
            )
            segments.append(segment)
            
            current_cell = self._get_stair_exit_cell(exit_cells)
        
        # 最后一段：从楼梯到目标
        final_floor_id = floor_sequence[-1]
        final_floor_node = self.floors[final_floor_id]
        final_path = self._compute_path_to_cells(
            final_floor_node,
            current_cell,
            target_cells,
            blocked=blocked_map.get(final_floor_id),
            cost_field=cost_fields.get(final_floor_id),
        )
        
        if final_path:
            segment = self._create_path_segment(
                final_floor_id,
                final_floor_node.height,
                final_floor_node.grid,
                final_path,
                'walk',
            )
            segments.append(segment)
        
        return segments
    
    def _compute_single_floor_path(
        self,
        floor_id: str,
        start_cell: GridCoord,
        target_cells: List[GridCoord],
        *,
        blocked: Optional[Set[GridCoord]] = None,
        cost_field: Optional[Dict[GridCoord, float]] = None,
    ) -> List[PathSegment]:
        """计算单楼层路径"""
        floor_node = self.floors.get(floor_id)
        if not floor_node:
            return []
        
        grid_path = self._compute_path_to_cells(
            floor_node,
            start_cell,
            target_cells,
            blocked=blocked,
            cost_field=cost_field,
        )
        
        if not grid_path:
            return []
        
        segment = self._create_path_segment(
            floor_id,
            floor_node.height,
            floor_node.grid,
            grid_path,
            'walk',
        )
        return [segment]
    
    def _compute_path_to_cells(
        self,
        floor_node: FloorNode,
        start: GridCoord,
        targets: List[GridCoord],
        *,
        blocked: Optional[Set[GridCoord]] = None,
        cost_field: Optional[Dict[GridCoord, float]] = None,
    ) -> List[GridCoord]:
        """在单层内计算到目标单元格集合的最短路径"""
        best_path: List[GridCoord] = []
        best_length = math.inf
        
        for target in targets:
            path = astar(floor_node.grid, start, target, blocked=blocked, cost_field=cost_field)
            if path and len(path) < best_length:
                best_path = path
                best_length = len(path)
        
        return best_path
    
    def _find_floor_sequence(self, start_floor: str, target_floor: str) -> List[str]:
        """
        找到从起点楼层到目标楼层的楼层序列。
        简化版本：假设楼层按 floor1 < floor2 < floor3 排序。
        """
        floor_order = ['floor1', 'floor2', 'floor3']
        
        if start_floor not in floor_order or target_floor not in floor_order:
            return []
        
        start_idx = floor_order.index(start_floor)
        target_idx = floor_order.index(target_floor)
        
        if start_idx > target_idx:
            # 下楼
            return floor_order[target_idx:start_idx + 1][::-1]
        else:
            # 上楼（通常疏散不会上楼）
            return floor_order[start_idx:target_idx + 1]
    
    def _stairs_between_floors(
        self,
        from_floor: str,
        to_floor: str,
    ) -> List[Tuple[List[GridCoord], List[GridCoord]]]:
        """返回所有连接两个楼层的楼梯入口/出口集合"""
        candidates: List[Tuple[List[GridCoord], List[GridCoord]]] = []
        for connections in self.stair_connections.values():
            for conn_from, conn_to, entry_cells, exit_cells in connections:
                if conn_from == from_floor and conn_to == to_floor:
                    candidates.append((entry_cells, exit_cells))
        return candidates

    def _get_stair_exit_cell(
        self,
        exit_cells: List[GridCoord],
    ) -> GridCoord:
        """楼梯出口（使用第一个，可扩展为随机）"""
        if exit_cells:
            return exit_cells[0]
        return (0, 0)
    
    def _create_path_segment(
        self,
        floor_id: str,
        floor_height: float,
        grid: Grid,
        grid_path: List[GridCoord],
        segment_type: str,
    ) -> PathSegment:
        """创建路径段，将网格路径转换为世界坐标"""
        world_path: List[WorldCoord] = []
        origin = (grid.origin[0], floor_height, grid.origin[2])
        
        for x, y in grid_path:
            wx = origin[0] + (x + 0.5) * grid.cell_size
            wy = origin[1]
            wz = origin[2] + (y + 0.5) * grid.cell_size
            world_path.append((wx, wy, wz))
        
        return PathSegment(
            floor_id=floor_id,
            floor_height=floor_height,
            grid_path=grid_path,
            world_path=world_path,
            segment_type=segment_type,
        )
    
    def add_stair_transitions(self, segments: List[PathSegment]) -> List[WorldCoord]:
        """
        为路径段添加楼梯过渡动画。
        在楼层切换处插入垂直过渡节点。
        """
        if not segments:
            return []
        
        result: List[WorldCoord] = []
        
        for i, segment in enumerate(segments):
            result.extend(segment.world_path)
            
            # 如果下一段是不同楼层，添加过渡
            if i < len(segments) - 1:
                next_segment = segments[i + 1]
                if segment.floor_height != next_segment.floor_height:
                    # 添加垂直过渡
                    last_point = segment.world_path[-1]
                    next_point = next_segment.world_path[0]
                    
                    # 中间点（垂直下降）
                    mid_y = (last_point[1] + next_point[1]) / 2
                    mid_point = (last_point[0], mid_y, last_point[2])
                    result.append(mid_point)
        
        return result
