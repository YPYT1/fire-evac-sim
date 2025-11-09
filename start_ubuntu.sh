#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
BACKEND_LOG="${LOG_DIR}/backend.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"

REQUIRED_PYTHON_MINOR=11
REQUIRED_NODE_MAJOR=18

export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"

info() { printf '>>> %s\n' "$*"; }
warn() { printf '>>> [WARN] %s\n' "$*" >&2; }
err() { printf '>>> [ERROR] %s\n' "$*" >&2; }

if [[ $# -gt 0 ]]; then
  warn "检测到额外参数：$*，本脚本暂不支持这些参数，将忽略。"
fi

SUDO_CMD=()
run_sudo() {
  if [[ ${#SUDO_CMD[@]} -eq 0 ]]; then
    "$@"
  else
    "${SUDO_CMD[@]}" "$@"
  fi
}

if [[ ${EUID} -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO_CMD=(sudo)
  else
    err "需要 root 权限安装依赖，请使用 sudo 运行此脚本。"
    exit 1
  fi
fi

ensure_ubuntu() {
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    if [[ "${ID}" != "ubuntu" && "${ID_LIKE:-}" != *"ubuntu"* ]]; then
      warn "当前系统 (${PRETTY_NAME:-unknown}) 非 Ubuntu，后续操作可能失败。"
    fi
  fi
  if ! command -v apt-get >/dev/null 2>&1; then
    err "未找到 apt-get，本脚本仅支持 Debian/Ubuntu 系统。"
    exit 1
  fi
}

version_ge() {
  local current=$1
  local required=$2
  dpkg --compare-versions "${current}" ge "${required}"
}

APT_PACKAGES=()
APT_UPDATED=false
queue_pkg() {
  local pkg=$1
  if dpkg -s "${pkg}" >/dev/null 2>&1; then
    return
  fi
  APT_PACKAGES+=("${pkg}")
}

run_apt_install() {
  if [[ ${#APT_PACKAGES[@]} -eq 0 ]]; then
    return
  fi
  info "安装缺失的 APT 软件包：${APT_PACKAGES[*]}"
  if [[ "${APT_UPDATED}" != true ]]; then
    run_sudo apt-get update
    APT_UPDATED=true
  fi
  run_sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y "${APT_PACKAGES[@]}"
  APT_PACKAGES=()
  hash -r
}

ensure_basic_packages() {
  queue_pkg curl
  queue_pkg git
  queue_pkg ca-certificates
  queue_pkg build-essential
  queue_pkg pkg-config
  queue_pkg python3
  queue_pkg python3-venv
  queue_pkg python3-pip
  queue_pkg python3-dev
  queue_pkg software-properties-common
  queue_pkg unzip
  queue_pkg libffi-dev
  queue_pkg cmake
  run_apt_install
}

PYTHON_CMD=""
resolve_python_cmd() {
  local version=""
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="$(command -v python3)"
    version="$(${PYTHON_CMD} -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
    if version_ge "${version}" "3.${REQUIRED_PYTHON_MINOR}"; then
      return
    fi
    warn "检测到 Python 版本 ${version}，低于要求的 3.${REQUIRED_PYTHON_MINOR}。"
  fi

  if command -v python3.${REQUIRED_PYTHON_MINOR} >/dev/null 2>&1; then
    PYTHON_CMD="$(command -v python3.${REQUIRED_PYTHON_MINOR})"
    return
  fi

  PYTHON_CMD=""
}

ensure_deadsnakes() {
  if apt-cache show "python3.${REQUIRED_PYTHON_MINOR}" >/dev/null 2>&1; then
    return
  fi

  if ! command -v add-apt-repository >/dev/null 2>&1; then
    warn "缺少 add-apt-repository，无法自动添加 Python 3.${REQUIRED_PYTHON_MINOR} 的软件源，可手动安装。"
    return
  fi

  info "添加 deadsnakes PPA 以获取 Python 3.${REQUIRED_PYTHON_MINOR}"
  run_sudo add-apt-repository -y ppa:deadsnakes/ppa
  APT_UPDATED=false
}

ensure_python() {
  resolve_python_cmd
  if [[ -n "${PYTHON_CMD}" ]]; then
    return
  fi

  ensure_deadsnakes
  queue_pkg "python3.${REQUIRED_PYTHON_MINOR}"
  queue_pkg "python3.${REQUIRED_PYTHON_MINOR}-venv"
  queue_pkg "python3.${REQUIRED_PYTHON_MINOR}-dev"
  run_apt_install

  if command -v python3.${REQUIRED_PYTHON_MINOR} >/dev/null 2>&1; then
    PYTHON_CMD="$(command -v python3.${REQUIRED_PYTHON_MINOR})"
    if ! command -v python3 >/dev/null 2>&1 || ! version_ge "$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')" "3.${REQUIRED_PYTHON_MINOR}"; then
      if [[ -x /usr/bin/python3.${REQUIRED_PYTHON_MINOR} ]]; then
        info "将 python3 默认指向 Python 3.${REQUIRED_PYTHON_MINOR}"
        run_sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.${REQUIRED_PYTHON_MINOR} 2 >/dev/null 2>&1 || true
      fi
    fi
    return
  fi

  err "无法安装或找到 Python 3.${REQUIRED_PYTHON_MINOR}，请检查软件源后重试。"
  exit 1
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

ensure_node_version() {
  local install_nodesource=false

  if command -v node >/dev/null 2>&1; then
    local current
    current="$(node --version | sed 's/^v//')"
    local major="${current%%.*}"
    if [[ -n "${major}" && "${major}" -ge ${REQUIRED_NODE_MAJOR} ]]; then
      return
    fi
    warn "检测到 Node.js 版本 (${current}) 低于要求，准备升级到 LTS 版本。"
    install_nodesource=true
  else
    warn "Node.js 未检测到，准备安装 Nodesource LTS 版本。"
    install_nodesource=true
  fi

  if [[ "${install_nodesource}" == true ]]; then
    queue_pkg ca-certificates
    queue_pkg gnupg
    run_apt_install
    local nodesource_script
    nodesource_script=\"$(mktemp /tmp/nodesource-setup.XXXXXX)\"
    curl -fsSL https://deb.nodesource.com/setup_20.x -o \"${nodesource_script}\"
    run_sudo bash \"${nodesource_script}\"
    rm -f \"${nodesource_script}\"
    run_sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs
    hash -r
  fi
}

ensure_env() {
  info "检查并安装缺失的依赖 ..."
  ensure_ubuntu
  ensure_basic_packages
  ensure_python
  resolve_python_cmd
  if [[ -z "${PYTHON_CMD}" ]]; then
    err "依赖安装后仍无法定位 Python 3.${REQUIRED_PYTHON_MINOR}。"
    exit 1
  fi
  export UV_PYTHON="${PYTHON_CMD}"
  ensure_uv
  ensure_bun
  ensure_node_version
  info "依赖初步准备完成。"
}

verify_env() {
  info "重新检查依赖版本 ..."
  local all_ok=true

  if ! command -v curl >/dev/null 2>&1; then
    warn "未检测到 curl"
    all_ok=false
  fi

  if ! command -v git >/dev/null 2>&1; then
    warn "未检测到 git"
    all_ok=false
  fi

  if [[ -z "${PYTHON_CMD}" ]]; then
    warn "未检测到 Python 3.${REQUIRED_PYTHON_MINOR}"
    all_ok=false
  elif ! command -v "${PYTHON_CMD}" >/dev/null 2>&1; then
    warn "未检测到 Python 命令：${PYTHON_CMD}"
    all_ok=false
  else
    info "Python 版本：$(${PYTHON_CMD} --version 2>&1)"
  fi

  if ! command -v uv >/dev/null 2>&1; then
    warn "未检测到 uv"
    all_ok=false
  else
    info "uv 版本：$(uv --version | head -n 1)"
  fi

  if ! command -v bun >/dev/null 2>&1; then
    warn "未检测到 Bun"
    all_ok=false
  else
    info "Bun 版本：$(bun --version | head -n 1)"
  fi

  if ! command -v node >/dev/null 2>&1; then
    warn "未检测到 Node.js"
    all_ok=false
  else
    local current
    current="$(node --version | sed 's/^v//')"
    local major="${current%%.*}"
    info "Node.js 版本：v${current}"
    if [[ -z "${major}" || "${major}" -lt ${REQUIRED_NODE_MAJOR} ]]; then
      warn "Node.js 主版本必须 >= ${REQUIRED_NODE_MAJOR}"
      all_ok=false
    fi
  fi

  if ! command -v npm >/dev/null 2>&1; then
    warn "未检测到 npm"
    all_ok=false
  fi

  if [[ "${all_ok}" != true ]]; then
    err "依赖验证失败，请根据提示修复后重新运行脚本。"
    exit 1
  fi
  info "依赖检查通过。"
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

  local LOCAL_RVO2="${ROOT_DIR}/third_party/python-rvo2"
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
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:5173" >/dev/null 2>&1 || true
  fi

  info "服务已启动"
  echo "    后端日志：${BACKEND_LOG}"
  echo "    前端日志：${FRONTEND_LOG}"
  echo "    浏览器可访问：http://localhost:5173"
  echo
  info "实时日志输出（Ctrl+C 退出）："
  tail -f "${BACKEND_LOG}" "${FRONTEND_LOG}" &
  TAIL_PID=$!

  wait "${BACK_PID}" "${FRONT_PID}" >/dev/null 2>&1 || true
  cleanup
}

ensure_env
verify_env
ensure_rvo2
start_services
