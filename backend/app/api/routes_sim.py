"""REST 接口：负责仿真控制命令。"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ..core.config import AppSettings, get_settings
from ..core.schemas import (
    SimReplanRequest,
    SimStartRequest,
    SimStartResponse,
    SimStatusResponse,
    SimStopRequest,
)
from ..dependencies import get_session_manager
from ..services.session_manager import SessionManager

router = APIRouter()


@router.post("/start", response_model=SimStartResponse)
async def start_simulation(
    payload: SimStartRequest,
    settings: AppSettings = Depends(get_settings),
    manager: SessionManager = Depends(get_session_manager),
) -> SimStartResponse:
    """启动仿真并返回会话 ID。"""
    sim_settings = settings.simulation
    overrides = payload.model_dump(exclude_unset=True)
    agent_overrides = overrides.get("agents", {})
    agent_updates: dict[str, float | int] = {}
    if "count" not in agent_overrides:
        agent_updates["count"] = sim_settings.agent_count
    if "speed_mean" not in agent_overrides:
        agent_updates["speed_mean"] = sim_settings.speed_mean
    if "speed_std" not in agent_overrides:
        agent_updates["speed_std"] = sim_settings.speed_std
    if agent_updates:
        payload = payload.model_copy(
            update={"agents": payload.agents.model_copy(update=agent_updates)}
        )

    response = manager.start(
        payload,
        sim_settings.tick_hz,
        sim_settings.avoidance_strategy,
        sim_settings.fire_decay,
    )
    return response


@router.post("/replan", status_code=status.HTTP_202_ACCEPTED)
async def replan_simulation(
    payload: SimReplanRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> dict[str, str]:
    """触发路径重规划。"""
    manager.replan(payload)
    return {"status": "accepted"}


@router.get("/status", response_model=SimStatusResponse)
async def get_simulation_status(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> SimStatusResponse:
    """查询仿真当前状态。"""
    try:
        return manager.status(session_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"session {session_id} not found",
        ) from exc


@router.post("/stop", status_code=status.HTTP_204_NO_CONTENT)
async def stop_simulation(
    payload: SimStopRequest,
    background_tasks: BackgroundTasks,
    manager: SessionManager = Depends(get_session_manager),
) -> None:
    """停止并清理仿真会话。"""
    background_tasks.add_task(manager.stop, payload.session_id)
