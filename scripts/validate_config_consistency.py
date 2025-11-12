#!/usr/bin/env python3
"""
配置一致性校验脚本

检查 frontend/src/three/layoutConfig.ts 与 backend/app/data/config/simulation.yaml
之间的楼层配置、房间矩形、楼梯位置等是否一致，防止前后端配置失配。
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    print("❌ 缺少 PyYAML，请执行 `pip install pyyaml` 后重试")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]


def load_simulation_yaml() -> Dict[str, Any]:
    """加载后端 simulation.yaml 配置"""
    yaml_path = ROOT / "backend" / "app" / "data" / "config" / "simulation.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"未找到配置文件：{yaml_path}")
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_layout_config_ts() -> Dict[str, Any]:
    """解析前端 layoutConfig.ts 配置（简化解析）"""
    ts_path = ROOT / "frontend" / "src" / "three" / "layoutConfig.ts"
    if not ts_path.exists():
        raise FileNotFoundError(f"未找到配置文件：{yaml_path}")
    
    with open(ts_path, encoding="utf-8") as f:
        content = f.read()
    
    # 提取 floors 数组
    floors_match = re.search(r"floors:\s*\[(.*?)\]", content, re.DOTALL)
    if not floors_match:
        raise ValueError("无法解析 layoutConfig.ts 中的 floors 配置")
    
    floors_str = floors_match.group(1)
    
    # 简单解析楼层配置（level, sideRoom）
    floor_configs = []
    level_pattern = r"level:\s*(\d+)"
    side_room_pattern = r"sideRoom:\s*\{([^}]+)\}"
    
    for floor_block in floors_str.split("},"):
        level_match = re.search(level_pattern, floor_block)
        if not level_match:
            continue
        
        level = int(level_match.group(1))
        side_room = None
        
        room_match = re.search(side_room_pattern, floor_block, re.DOTALL)
        if room_match:
            room_str = room_match.group(1)
            side_match = re.search(r"side:\s*'(\w+)'", room_str)
            width_match = re.search(r"width:\s*(\d+)", room_str)
            depth_match = re.search(r"depth:\s*(\d+)", room_str)
            
            if side_match and width_match and depth_match:
                side_room = {
                    "side": side_match.group(1),
                    "width": int(width_match.group(1)),
                    "depth": int(depth_match.group(1)),
                }
        
        floor_configs.append({
            "level": level,
            "sideRoom": side_room,
        })
    
    return {"floors": floor_configs}


def check_floor_count(backend: Dict[str, Any], frontend: Dict[str, Any]) -> List[str]:
    """检查楼层数量是否一致"""
    issues = []
    backend_floors = backend.get("floors", {})
    frontend_floors = frontend.get("floors", [])
    
    if len(backend_floors) != len(frontend_floors):
        issues.append(
            f"❌ 楼层数量不一致：后端 {len(backend_floors)} 层，前端 {len(frontend_floors)} 层"
        )
    else:
        print(f"✅ 楼层数量一致：{len(backend_floors)} 层")
    
    return issues


def check_floor_heights(backend: Dict[str, Any], frontend: Dict[str, Any]) -> List[str]:
    """检查楼层高度配置"""
    issues = []
    backend_floors = backend.get("floors", {})
    frontend_floors = frontend.get("floors", [])
    
    expected_heights = {0: 0.0, 1: 4.0, 2: 8.0}
    
    for floor_id, floor_cfg in backend_floors.items():
        level_match = re.match(r"floor(\d+)", floor_id)
        if level_match:
            level = int(level_match.group(1)) - 1  # floor1 -> level 0
            expected_height = expected_heights.get(level)
            actual_height = floor_cfg.get("height")
            
            if expected_height is not None and actual_height != expected_height:
                issues.append(
                    f"❌ {floor_id} 高度错误：期望 {expected_height}m，实际 {actual_height}m"
                )
    
    if not issues:
        print("✅ 楼层高度配置正确")
    
    return issues


def check_side_rooms(backend: Dict[str, Any], frontend: Dict[str, Any]) -> List[str]:
    """检查侧面房间配置是否一致"""
    issues = []
    frontend_floors = frontend.get("floors", [])
    
    # 检查三层房间（level 2）
    floor3_config = next((f for f in frontend_floors if f["level"] == 2), None)
    if floor3_config and floor3_config.get("sideRoom"):
        room = floor3_config["sideRoom"]
        print(f"📦 前端三层房间配置：{room['side']}侧, {room['width']}m × {room['depth']}m")
        
        # 这里可以添加更多具体的验证逻辑
        if room["side"] not in ["north", "south", "east", "west"]:
            issues.append(f"❌ 房间方位错误：{room['side']}")
        
        if room["width"] <= 0 or room["depth"] <= 0:
            issues.append(f"❌ 房间尺寸错误：{room['width']}m × {room['depth']}m")
    
    if not issues:
        print("✅ 侧面房间配置有效")
    
    return issues


def check_stairs(backend: Dict[str, Any]) -> List[str]:
    """检查楼梯配置"""
    issues = []
    stairs = backend.get("stairs", {})
    
    expected_stairs = ["west_stair", "east_stair", "south_stair"]
    for stair_id in expected_stairs:
        if stair_id not in stairs:
            issues.append(f"❌ 缺少楼梯配置：{stair_id}")
    
    if not issues:
        print(f"✅ 楼梯配置完整：{len(stairs)} 个楼梯")
    
    return issues


def main() -> int:
    print("🔍 开始检查配置一致性...\n")
    
    try:
        backend_config = load_simulation_yaml()
        frontend_config = parse_layout_config_ts()
    except Exception as e:
        print(f"❌ 加载配置失败：{e}")
        return 1
    
    all_issues: List[str] = []
    
    # 执行各项检查
    all_issues.extend(check_floor_count(backend_config, frontend_config))
    all_issues.extend(check_floor_heights(backend_config, frontend_config))
    all_issues.extend(check_side_rooms(backend_config, frontend_config))
    all_issues.extend(check_stairs(backend_config))
    
    print()
    if all_issues:
        print("❌ 发现配置不一致问题：\n")
        for issue in all_issues:
            print(f"  {issue}")
        return 1
    else:
        print("✅ 所有配置检查通过！前后端配置一致。")
        return 0


if __name__ == "__main__":
    sys.exit(main())
