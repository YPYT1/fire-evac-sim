"""应用配置与仿真参数加载。"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SimulationSettings(BaseModel):
    """仿真运行的静态配置。"""

    mode: Literal["floor1", "floor2", "floor3"] = "floor1"
    tick_hz: int = Field(default=20, ge=1, description="仿真刷新频率（Hz）")
    agent_count: int = Field(default=200, ge=1)
    speed_mean: float = Field(default=1.3, gt=0)
    speed_std: float = Field(default=0.2, ge=0)
    map_name: str = Field(default="canteen_map.json")
    map_cell_size: float = Field(default=1.0, gt=0)
    map_origin: tuple[float, float, float] = Field(default=(0.0, 0.0, 0.0))
    map_exits: list[dict] = Field(default_factory=list)
    start_regions: list[dict] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    fire_decay: float = Field(default=0.95, ge=0.0, le=1.0, description="火源扩散衰减系数")
    avoidance_strategy: Literal["rvo2", "rvo2_py", "simple"] = Field(
        default="rvo2",
        description="避障策略，支持 RVO2、rvo2-py 与 simple 简化策略回退。",
    )

    @field_validator("map_name")
    def _validate_map(cls, value: str) -> str:
        if not value:
            raise ValueError("map_name 不能为空")
        return value


class AppSettings(BaseModel):
    """后端应用层配置。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    backend_host: str = Field(default=os.getenv("BACKEND_HOST", "127.0.0.1"))
    backend_port: int = Field(default=int(os.getenv("BACKEND_PORT", "8000")), ge=1, le=65535)
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    debug: bool = Field(default=os.getenv("DEBUG", "0") == "1")
    simulation_config_path: Path = Field(
        default=Path(os.getenv("SIM_CONFIG_PATH", "backend/app/data/config/simulation.yaml")).resolve()
    )

    @property
    def simulation(self) -> SimulationSettings:
        """读取并缓存仿真配置文件。"""
        return load_simulation_config(self.simulation_config_path)

    @property
    def logger(self) -> logging.Logger:
        """提供统一的命名 logger。"""
        logger = logging.getLogger("fire_evac_sim")
        if not logger.handlers:
            logging.basicConfig(level=self.log_level.upper())
        return logger


def load_simulation_config(path: Path) -> SimulationSettings:
    """从 YAML 文件加载仿真配置。"""
    if not path.exists():
        raise FileNotFoundError(f"未找到仿真配置文件: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw: dict[str, Any] = yaml.safe_load(file) or {}

    payload: dict[str, Any] = dict(raw)

    sim_section = raw.get("sim")
    if isinstance(sim_section, dict):
        payload.update(sim_section)

    agents_section = raw.get("agents")
    if isinstance(agents_section, dict):
        payload.setdefault("agent_count", agents_section.get("count"))
        speed_cfg = agents_section.get("speed", {})
        if isinstance(speed_cfg, dict):
            payload.setdefault("speed_mean", speed_cfg.get("mean"))
            payload.setdefault("speed_std", speed_cfg.get("std"))
        if "start_region" in agents_section:
            payload.setdefault("start_regions", agents_section.get("start_region"))

    map_section = raw.get("map")
    if isinstance(map_section, dict):
        payload.setdefault("map_name", map_section.get("file"))
        payload.setdefault("map_cell_size", map_section.get("cell_size"))
        payload.setdefault("map_origin", tuple(map_section.get("origin", (0.0, 0.0, 0.0))))
        payload.setdefault("map_exits", map_section.get("exits", []))

    fire_section = raw.get("fire")
    if isinstance(fire_section, dict):
        if "diffusion_decay" in fire_section:
            payload.setdefault("fire_decay", fire_section.get("diffusion_decay"))
        if "decay" in fire_section:
            payload.setdefault("fire_decay", fire_section.get("decay"))

    # Fallback：若部分关键参数仍为空，则使用默认值填充
    defaults = {
        "mode": "floor1",
        "tick_hz": 20,
        "agent_count": 200,
        "speed_mean": 1.3,
        "speed_std": 0.2,
        "map_name": "canteen_map.json",
        "map_cell_size": 1.0,
        "map_origin": (-30.0, 0.0, -30.0),
        "map_exits": [],
        "start_regions": [],
        "goals": [],
        "avoidance_strategy": "rvo2",
        "fire_decay": 0.95,
    }
    for key, value in defaults.items():
        payload.setdefault(key, value)

    return SimulationSettings(**payload)


@lru_cache()
def get_settings() -> AppSettings:
    """懒加载应用配置，适用于依赖注入。"""
    return AppSettings()
