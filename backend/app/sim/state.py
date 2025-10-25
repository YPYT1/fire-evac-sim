"""仿真状态容器，统一维护代理、火源与地图数据。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from ..core.schemas import AgentState, FireSource


@dataclass
class SimulationState:
    """内存态的仿真快照。后续可替换为 numpy/numba 数据结构。"""

    session_id: str
    tick_hz: int
    agents: Dict[int, AgentState] = field(default_factory=dict)
    fires: List[FireSource] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    total_agents: int = 0
    tick_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    fire_decay: float = 0.95
    speed_mean: float = 1.3
    speed_std: float = 0.2

    def update_agent(self, state: AgentState) -> None:
        """更新/新增代理状态。"""
        self.agents[state.id] = state

    def remove_agent(self, agent_id: int) -> None:
        """删除代理，示例实现用于占位。"""
        self.agents.pop(agent_id, None)

    def advance(self, dt: float) -> None:
        """推进一次仿真，当前逻辑仅做匀速位移占位。"""
        for agent in list(self.agents.values()):
            px, py, pz = agent.position
            vx, vy, vz = agent.velocity
            new_state = AgentState(
                id=agent.id,
                position=(px + vx * dt, py + vy * dt, pz + vz * dt),
                velocity=agent.velocity,
            )
            self.agents[agent.id] = new_state
        self.tick_count += 1
        self.last_updated = datetime.utcnow()

    def stats(self) -> dict:
        """计算快照统计数据，供状态面板使用。"""
        active_agents = len(self.agents)
        if active_agents:
            average_speed = sum(
                (vx ** 2 + vy ** 2 + vz ** 2) ** 0.5
                for vx, vy, vz in (agent.velocity for agent in self.agents.values())
            ) / active_agents
        else:
            average_speed = 0.0
        if self.total_agents > 0:
            congestion_ratio = min(1.0, active_agents / self.total_agents)
        else:
            congestion_ratio = 0.0
        return {
            "agent_count": active_agents,
            "active_agents": active_agents,
            "average_speed": average_speed,
            "congestion_ratio": congestion_ratio,
            "speed_mean": self.speed_mean,
            "speed_std": self.speed_std,
            "fire_decay": self.fire_decay,
        }

    def snapshot(self) -> dict:
        """导出可序列化快照，供 WebSocket 推送。"""
        return {
            "session_id": self.session_id,
            "tick_hz": self.tick_hz,
            "tick": self.tick_count,
            "agents": [agent.dict() for agent in self.agents.values()],
            "fires": [fire.dict() for fire in self.fires],
            "goals": self.goals,
            "stats": self.stats(),
            "updated_at": self.last_updated.isoformat(),
        }
