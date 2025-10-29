"""Pydantic 数据模型：用于请求/响应与内部数据交换。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FireSource(BaseModel):
    """火源位置与权重。"""

    position: tuple[float, float, float] = Field(..., description="世界坐标 (x, y, z)")
    intensity: float = Field(default=1.0, ge=0.0, description="火焰强度，用于代价场加权")


class AgentSpawnConfig(BaseModel):
    """代理生成参数。"""

    count: int = Field(default=200, ge=1)
    speed_mean: float = Field(default=1.3, gt=0)
    speed_std: float = Field(default=0.2, ge=0)


class SimStartRequest(BaseModel):
    """启动仿真请求体。"""

    mode: Literal["floor1", "floor2", "floor3"] = "floor1"
    fires: list[FireSource] | None = Field(default=None, description="覆盖默认火点分布")
    agents: AgentSpawnConfig = Field(default_factory=AgentSpawnConfig)
    goals: list[str] = Field(default_factory=list, description="出口或目标点的标识符")
    avoidance_strategy: Literal["rvo2", "rvo2_py", "simple"] | None = Field(
        default=None,
        description="可选的避障策略覆盖项，缺省时使用配置文件默认值。",
    )


class SimStartResponse(BaseModel):
    """启动仿真响应。"""

    session_id: str
    tick_hz: int
    avoidance_strategy: Literal["rvo2", "rvo2_py", "simple"]


class SimReplanRequest(BaseModel):
    """重规划请求。"""

    session_id: str
    fires: list[FireSource]
    reason: str | None = None


class AgentState(BaseModel):
    """单个代理的状态。"""

    id: int
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]


class SimStatusResponse(BaseModel):
    """仿真状态查询结果。"""

    session_id: str
    agent_count: int
    active_agents: int
    average_speed: float
    congestion_ratio: float
    updated_at: datetime
    avoidance_strategy: Literal["rvo2", "rvo2_py", "simple"]
    tick_hz: int
    speed_mean: float
    speed_std: float
    fire_decay: float


class SimStopRequest(BaseModel):
    """停止仿真请求。"""

    session_id: str
