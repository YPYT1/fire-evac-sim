"""FastAPI 应用入口，统一挂载 REST 与 WebSocket 接口。"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes_sim import router as sim_router
from .api.ws import router as ws_router
from .core.config import get_settings


def create_app() -> FastAPI:
    """构建并配置 FastAPI 应用实例。"""
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.logger.info(
            "⚙️ Fire Evac Sim backend starting on %s:%s",
            settings.backend_host,
            settings.backend_port,
        )
        try:
            yield
        finally:
            settings.logger.info("👋 Fire Evac Sim backend shutting down")

    app = FastAPI(
        title="Fire Evacuation Simulation API",
        description="火灾疏散仿真后端：提供 REST 控制面与实时 WebSocket 状态同步。",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        lifespan=lifespan,
    )

    app.include_router(sim_router, prefix="/sim", tags=["simulation"])
    app.include_router(ws_router, prefix="/ws", tags=["websocket"])

    return app


# 供 uvicorn 直接加载
app = create_app()
