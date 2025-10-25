#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
BACKEND_LOG="${LOG_DIR}/backend.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"

export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"

info() { printf '>>> %s\n' "$*"; }
warn() { printf '>>> [WARN] %s\n' "$*" >&2; }

ensure_homebrew() {
  if command -v brew >/dev/null 2>&1; then
    if [[ -x "/opt/homebrew/bin/brew" ]]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -x "/usr/local/bin/brew" ]]; then
      eval "$(/usr/local/bin/brew shellenv)"
    fi
    return
  fi
  info "安装 Homebrew ..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if [[ -x "/opt/homebrew/bin/brew" ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x "/usr/local/bin/brew" ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  else
    warn "Homebrew 安装后未找到可执行文件，请检查输出。"
  fi
}

ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    return
  fi
  ensure_homebrew
  info "安装 Python 3（brew install python@3.11）..."
  brew install python@3.11
  hash -r
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi
  info "安装 uv ..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  hash -r
}

ensure_bun() {
  if command -v bun >/dev/null 2>&1; then
    return
  fi
  info "安装 Bun ..."
  curl -fsSL https://bun.sh/install | bash
  export BUN_INSTALL="${HOME}/.bun"
  export PATH="$BUN_INSTALL/bin:$PATH"
  hash -r
}

ensure_node() {
  ensure_homebrew
  local required_major=18
  if command -v node >/dev/null 2>&1; then
    local current
    current="$(node --version | sed 's/^v//')"
    local major="${current%%.*}"
    if [[ -n "${major}" && "${major}" -ge ${required_major} ]]; then
      return
    fi
    warn "检测到 Node.js 版本 (${current}) 低于要求，尝试通过 Homebrew 升级。"
    brew upgrade node || brew install node
  else
    info "安装 Node.js ..."
    brew install node
  fi
  hash -r
}

ensure_curl() {
  if command -v curl >/dev/null 2>&1; then
    return
  fi
  ensure_homebrew
  info "安装 curl ..."
  brew install curl
  hash -r
}

ensure_env() {
  info "检查并安装缺失的依赖 ..."
  ensure_curl
  ensure_python
  ensure_uv
  ensure_bun
  ensure_node
  info "依赖检查完成："
  python3 --version
  uv --version
  bun --version
  node --version
}

ensure_rvo2() {
  if uv pip show python-rvo2 >/dev/null 2>&1; then
    info "检测到 python-rvo2 已安装。"
    return
  fi
  if uv pip show rvo2-py >/dev/null 2>&1; then
    info "检测到 rvo2-py 已安装。"
    return
  fi

  LOCAL_RVO2="${ROOT_DIR}/third_party/python-rvo2"
  if [[ -d "${LOCAL_RVO2}" ]]; then
    info "尝试从 third_party/python-rvo2 安装本地包 ..."
    if uv pip install "${LOCAL_RVO2}" >/dev/null 2>&1; then
      info "已从本地源码安装 python-rvo2。"
      return
    fi
    warn "本地 python-rvo2 安装失败，将尝试网络安装。"
  fi

  info "尝试安装高性能避障库 python-rvo2 ..."
  if uv pip install python-rvo2 >/dev/null 2>&1; then
    info "python-rvo2 安装成功。"
    return
  fi

  warn "python-rvo2 安装失败，将自动安装纯 Python 版本 rvo2-py。"
  if uv pip install rvo2-py >/dev/null 2>&1; then
    info "rvo2-py 安装完成，可作为临时避障方案。"
    return
  fi

  warn "rvo2-py 安装也失败，将继续使用 simple 避障策略。"
}

start_services() {
  mkdir -p "${LOG_DIR}"
  : >"${BACKEND_LOG}"
  : >"${FRONTEND_LOG}"

  info "同步后端依赖（uv sync）"
  uv sync >/dev/null

  info "同步前端依赖（bun install）"
  (cd "${ROOT_DIR}/frontend" && bun install >/dev/null)

  cleanup() {
    echo
    info "停止服务 ..."
    [[ -n "${BACK_PID:-}" ]] && kill "${BACK_PID}" >/dev/null 2>&1 || true
    [[ -n "${FRONT_PID:-}" ]] && kill "${FRONT_PID}" >/dev/null 2>&1 || true
    [[ -n "${TAIL_PID:-}" ]] && kill "${TAIL_PID}" >/dev/null 2>&1 || true
    wait >/dev/null 2>&1 || true
    info "服务已停止，日志保留于 ${LOG_DIR}"
  }
  trap cleanup INT TERM

  info "启动后端（uvicorn）"
  uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --log-level info >"${BACKEND_LOG}" 2>&1 &
  BACK_PID=$!

  info "启动前端（bun dev）"
  (cd "${ROOT_DIR}/frontend" && bun dev --host) >"${FRONTEND_LOG}" 2>&1 &
  FRONT_PID=$!

  sleep 2
  open "http://localhost:5173" >/dev/null 2>&1 || true

  info "服务已启动"
  echo "    后端日志：${BACKEND_LOG}"
  echo "    前端日志：${FRONTEND_LOG}"
  echo "    浏览器已尝试打开 http://localhost:5173"
  echo
  info "实时日志输出（Ctrl+C 退出）："
  tail -f "${BACKEND_LOG}" "${FRONTEND_LOG}" &
  TAIL_PID=$!

  wait "${BACK_PID}" "${FRONT_PID}" >/dev/null 2>&1 || true
  cleanup
}

ensure_env
ensure_rvo2
start_services
