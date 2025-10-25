"""避障策略适配层：支持 RVO2、rvo2-py 与简化 fallback。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

try:  # pragma: no cover - 若未安装 python-rvo2，仅记录占位
    import rvo2  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    rvo2 = None  # type: ignore

try:  # pragma: no cover - 纯 Python 版本的 ORCA
    import rvo2_py  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    rvo2_py = None  # type: ignore

Vector = Tuple[float, float]
LOGGER = logging.getLogger(__name__)

__all__ = ["AgentConfig", "RVOManager"]


@dataclass
class AgentConfig:
    """代理参数，用于初始化不同策略时的公共配置。"""

    max_speed: float = 2.0
    neighbor_dist: float = 5.0
    time_horizon: float = 5.0
    radius: float = 0.3


class _BaseAvoidance:
    """避障策略统一接口。"""

    name: str

    def add_agent(self, position: Vector, config: AgentConfig) -> int:
        raise NotImplementedError

    def set_preferred_velocity(self, agent_id: int, velocity: Vector) -> None:
        raise NotImplementedError

    def step(self) -> None:
        raise NotImplementedError

    def get_agent_position(self, agent_id: int) -> Vector:
        raise NotImplementedError


class _SimpleAvoidance(_BaseAvoidance):
    """最简单的匀速避障占位策略。"""

    def __init__(self, timestep: float) -> None:
        self.name = "simple"
        self._timestep = timestep
        self._positions: List[Vector] = []
        self._velocities: List[Vector] = []

    def add_agent(self, position: Vector, config: AgentConfig) -> int:  # noqa: ARG002
        self._positions.append(position)
        self._velocities.append((0.0, 0.0))
        return len(self._positions) - 1

    def set_preferred_velocity(self, agent_id: int, velocity: Vector) -> None:
        if 0 <= agent_id < len(self._velocities):
            self._velocities[agent_id] = velocity

    def step(self) -> None:
        updated: List[Vector] = []
        for (x, y), (vx, vy) in zip(self._positions, self._velocities):
            updated.append((x + vx * self._timestep, y + vy * self._timestep))
        self._positions = updated

    def get_agent_position(self, agent_id: int) -> Vector:
        if 0 <= agent_id < len(self._positions):
            return self._positions[agent_id]
        return 0.0, 0.0


class _RVO2LikeAvoidance(_BaseAvoidance):
    """对 RVO2/rvo2-py 的统一封装。"""

    def __init__(self, simulator: object, name: str) -> None:
        self.name = name
        self._sim = simulator
        self._agents: List[int] = []

    def add_agent(self, position: Vector, config: AgentConfig) -> int:
        agent_id = self._sim.addAgent(
            position,
            config.neighbor_dist,
            10,
            config.time_horizon,
            config.time_horizon,
            config.radius,
            config.max_speed,
        )
        self._agents.append(agent_id)
        return agent_id

    def set_preferred_velocity(self, agent_id: int, velocity: Vector) -> None:
        self._sim.setAgentPrefVelocity(agent_id, velocity)

    def step(self) -> None:
        self._sim.doStep()

    def get_agent_position(self, agent_id: int) -> Vector:
        return self._sim.getAgentPosition(agent_id)


def _build_rvo2(timestep: float) -> Optional[_BaseAvoidance]:
    if rvo2 is None:
        return None
    simulator = rvo2.PyRVOSimulator(timestep, 5.0, 10, 5.0, 5.0, 0.3, 2.0)
    return _RVO2LikeAvoidance(simulator, "rvo2")


def _build_rvo2_py(timestep: float) -> Optional[_BaseAvoidance]:
    if rvo2_py is None:
        return None
    factory = getattr(rvo2_py, "PyRVOSimulator", None)
    if factory is None:
        return None
    simulator = factory(timestep, 5.0, 10, 5.0, 5.0, 0.3, 2.0)
    return _RVO2LikeAvoidance(simulator, "rvo2_py")


class RVOManager:
    """根据配置选择合适的避障实现，并暴露统一 API。"""

    def __init__(self, strategy: str = "rvo2", timestep: float = 0.05) -> None:
        self.requested_strategy = strategy
        self.timestep = timestep
        self._impl = self._init_strategy(strategy, timestep)
        self.effective_strategy = self._impl.name

    def _init_strategy(self, strategy: str, timestep: float) -> _BaseAvoidance:
        builders: Dict[str, Callable[[float], Optional[_BaseAvoidance]]] = {
            "rvo2": _build_rvo2,
            "rvo2_py": _build_rvo2_py,
        }
        builder = builders.get(strategy)
        if builder:
            impl = builder(timestep)
            if impl is not None:
                return impl
            LOGGER.warning("%s 未安装或初始化失败，回退 simple 避障。", strategy)
        return _SimpleAvoidance(timestep)

    def add_agent(self, position: Vector, config: AgentConfig | None = None) -> int:
        cfg = config or AgentConfig()
        return self._impl.add_agent(position, cfg)

    def set_preferred_velocity(self, agent_id: int, velocity: Vector) -> None:
        self._impl.set_preferred_velocity(agent_id, velocity)

    def step(self) -> None:
        self._impl.step()

    def get_agent_position(self, agent_id: int) -> Vector:
        return self._impl.get_agent_position(agent_id)
