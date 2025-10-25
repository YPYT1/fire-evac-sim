"""FastAPI 依赖注入入口。"""

from __future__ import annotations

from .services.session_manager import SessionManager, session_manager


def get_session_manager() -> SessionManager:
    """返回全局 SessionManager 实例，供 Depends 使用。"""
    return session_manager
