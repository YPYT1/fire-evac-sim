"""会话管理：负责仿真实例的生命周期与调度。"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Literal, Optional

from ..core.schemas import (
    AgentSpawnConfig,
    FireSource,
    SimReplanRequest,
    SimStartRequest,
    SimStartResponse,
    SimStatusResponse,
)
from ..sim.state import SimulationState


class SessionManager:
    """管理仿真会话、后台循环与火点更新。"""

    def __init__(self) -> None:
        self._sessions: Dict[str, dict] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    def start(
        self,
        payload: SimStartRequest,
        tick_hz: int,
        default_strategy: Literal["rvo2", "rvo2_py", "simple"],
        fire_decay: float,
    ) -> SimStartResponse:
        """创建仿真会话并启动后台循环。"""
        session_id = f"demo-{len(self._sessions) + 1}"
        strategy = payload.avoidance_strategy or default_strategy
        state = SimulationState(
            session_id=session_id,
            tick_hz=tick_hz,
            goals=payload.goals,
            total_agents=payload.agents.count,
            fire_decay=fire_decay,
        )
        state.fires = payload.fires or []
        state.speed_mean = payload.agents.speed_mean
        state.speed_std = payload.agents.speed_std

        self._sessions[session_id] = {
            "payload": payload,
            "created_at": datetime.utcnow(),
            "tick_hz": tick_hz,
            "avoidance_strategy": strategy,
            "state": state,
            "fires": payload.fires or [],
            "fire_decay": fire_decay,
        }
        self._start_loop(session_id, state)
        return SimStartResponse(session_id=session_id, tick_hz=tick_hz, avoidance_strategy=strategy)

    def status(self, session_id: str) -> SimStatusResponse:
        """返回仿真当前状态指标。"""
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        state: SimulationState = session["state"]
        stats = state.stats()
        return SimStatusResponse(
            session_id=session_id,
            agent_count=state.total_agents,
            active_agents=stats["active_agents"],
            average_speed=stats["average_speed"],
            congestion_ratio=stats["congestion_ratio"],
            updated_at=state.last_updated,
            avoidance_strategy=session.get("avoidance_strategy", "rvo2"),
            tick_hz=state.tick_hz,
            speed_mean=stats["speed_mean"],
            speed_std=stats["speed_std"],
            fire_decay=stats["fire_decay"],
        )

    def stop(self, session_id: str) -> None:
        """终止会话并取消后台任务。"""
        self._sessions.pop(session_id, None)
        task = self._tasks.pop(session_id, None)
        if task:
            task.cancel()

    def replan(self, payload: SimReplanRequest) -> None:
        """更新会话火点数据，触发后续重规划。"""
        session = self._sessions.get(payload.session_id)
        if session is None:
            raise KeyError(payload.session_id)
        fires: list[FireSource] = payload.fires
        session["fires"] = fires
        state: SimulationState = session["state"]
        state.fires = fires
        session.setdefault("replans", []).append(payload)

    def get_state(self, session_id: str) -> Optional[SimulationState]:
        """提供给 WebSocket 层的快照读取接口。"""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        return session["state"]

    def _start_loop(self, session_id: str, state: SimulationState) -> None:
        async def runner() -> None:
            tick_interval = 1 / state.tick_hz
            while session_id in self._sessions:
                state.advance(tick_interval)
                await asyncio.sleep(tick_interval)

        loop = asyncio.get_event_loop()
        self._tasks[session_id] = loop.create_task(runner())


# 全局单例，后续可替换为依赖注入
session_manager = SessionManager()
