#!/usr/bin/env bash
set -euo pipefail

# 使用 uv 启动开发服务器
uv run uvicorn backend.app.main:app --reload --host "${BACKEND_HOST:-127.0.0.1}" --port "${BACKEND_PORT:-8000}"
