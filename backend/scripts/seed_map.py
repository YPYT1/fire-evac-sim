"""示例脚本：将平面图转换为 demo_map.json。"""

from __future__ import annotations

from pathlib import Path

import json

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "maps" / "demo_map.json"


def main() -> None:
    """生成一个 10x10 的占位栅格。"""
    grid = {
        "width": 10,
        "height": 10,
        "cellSize": 1.0,
        "cells": [[{"walkable": True} for _ in range(10)] for _ in range(10)],
        "exits": {"exitA": {"rect": [9, 4, 1, 2]}},
    }
    OUTPUT_PATH.write_text(json.dumps(grid, indent=2), encoding="utf-8")
    print(f"Wrote placeholder map to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
