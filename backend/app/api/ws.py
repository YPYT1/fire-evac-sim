"""WebSocket 接口：向前端推送仿真状态。"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ..dependencies import get_session_manager
from ..services.session_manager import SessionManager

router = APIRouter()


@router.websocket("/sim/{session_id}")
async def simulation_socket(
    websocket: WebSocket,
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> None:
    """推送实时仿真状态，如果会话不存在则立即断开。"""

    await websocket.accept()
    state = manager.get_state(session_id)
    if state is None:
        await websocket.send_json({"type": "error", "reason": "session_not_found"})
        await websocket.close()
        return

    await websocket.send_json({"type": "hello", "session_id": session_id})

    try:
        while True:
            snapshot = state.snapshot()
            await websocket.send_json({"type": "state", **snapshot})
            await asyncio.sleep(1 / state.tick_hz)
    except WebSocketDisconnect:
        await websocket.close()
