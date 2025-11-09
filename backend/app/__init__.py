"""火灾疏散模拟 backend package."""

__all__ = ["create_app"]

try:
    from .main import create_app
except ModuleNotFoundError as exc:  # pragma: no cover - dev 环境可能缺少 fastapi
    if exc.name != "fastapi":
        raise

    def create_app():  # type: ignore
        raise RuntimeError("FastAPI 未安装，无法创建应用实例。")
