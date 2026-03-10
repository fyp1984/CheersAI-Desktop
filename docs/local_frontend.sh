#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/web"
FRONTEND_LOG_DIR="${ROOT_DIR}/logs"
FRONTEND_LOG_FILE="${FRONTEND_LOG_DIR}/web-dev.log"
FRONTEND_PID_FILE="${FRONTEND_DIR}/.next_dev.pid"

ensure_pnpm() {
  if ! command -v pnpm >/dev/null 2>&1; then
    echo "ERROR: 'pnpm' 命令不存在，请先安装 pnpm 并确保其在 PATH 中。" >&2
    exit 1
  fi
}

warn_node_version() {
  if ! command -v node >/dev/null 2>&1; then
    echo "WARN: 未检测到 node 命令，请确认 Node.js 已安装。"
    return
  fi

  local node_ver major
  node_ver="$(node -v 2>/dev/null || echo "")"
  # 使用 Node 自己解析主版本号，避免 sed 在 macOS 上的兼容性问题
  major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo "")"

  if [[ -n "${major}" ]] && (( major < 24 )); then
    echo "WARN: 当前 Node 版本为 ${node_ver}，工程推荐 node >= 24，建议后续升级。"
  fi
}

start_frontend() {
  ensure_pnpm
  warn_node_version

  mkdir -p "${FRONTEND_LOG_DIR}"

  if [[ -f "${FRONTEND_PID_FILE}" ]]; then
    local pid
    pid="$(cat "${FRONTEND_PID_FILE}" || true)"
    if [[ -n "${pid}" ]] && ps -p "${pid}" >/dev/null 2>&1; then
      echo "[INFO] 前端已在运行，PID=${pid}。如需重启请先执行: $0 stop 或 $0 restart"
      return
    else
      rm -f "${FRONTEND_PID_FILE}"
    fi
  fi

  # 强制清除 DEBUG 环境变量，防止日志暴涨 (15MB/10s)
  export DEBUG=""

  echo "[START] 启动前端 (pnpm run dev)..."
  cd "${FRONTEND_DIR}"
  nohup pnpm run dev > "${FRONTEND_LOG_FILE}" 2>&1 &
  local new_pid=$!
  echo "${new_pid}" > "${FRONTEND_PID_FILE}"
  echo "[OK] 前端已后台启动，PID=${new_pid}，日志: ${FRONTEND_LOG_FILE}"
}

stop_frontend() {
  if [[ ! -f "${FRONTEND_PID_FILE}" ]]; then
    echo "[INFO] 未找到前端 PID 文件，可能前端未运行。"
    return
  fi

  local pid
  pid="$(cat "${FRONTEND_PID_FILE}" || true)"
  if [[ -z "${pid}" ]]; then
    echo "[WARN] PID 文件为空，删除并返回。"
    rm -f "${FRONTEND_PID_FILE}"
    return
  fi

  if ps -p "${pid}" >/dev/null 2>&1; then
    echo "[STOP] 停止前端进程，PID=${pid}..."
    kill "${pid}" || true
    sleep 2
    if ps -p "${pid}" >/dev/null 2>&1; then
      echo "[WARN] 前端未正常退出，发送 SIGKILL..."
      kill -9 "${pid}" || true
    fi
  else
    echo "[INFO] PID=${pid} 的进程不存在，删除 PID 文件。"
  fi

  rm -f "${FRONTEND_PID_FILE}"
  echo "[OK] 前端已停止。"
}

status() {
  echo "== 前端进程状态 =="
  if [[ -f "${FRONTEND_PID_FILE}" ]]; then
    local pid
    pid="$(cat "${FRONTEND_PID_FILE}" || true)"
    if [[ -n "${pid}" ]] && ps -p "${pid}" >/dev/null 2>&1; then
      echo "前端运行中，PID=${pid}"
    else
      echo "前端未运行（PID 文件存在但无对应进程），建议执行: $0 start 或手动删除 ${FRONTEND_PID_FILE}"
    fi
  else
    echo "前端未运行（未找到 PID 文件）。"
  fi
}

show_logs() {
  if [[ ! -f "${FRONTEND_LOG_FILE}" ]]; then
    echo "[INFO] 日志文件不存在: ${FRONTEND_LOG_FILE}"
    return
  fi
  echo "[LOGS] tail -n 100 -f ${FRONTEND_LOG_FILE}"
  tail -n 100 -f "${FRONTEND_LOG_FILE}"
}

case "${1:-}" in
  start)
    start_frontend
    ;;
  stop)
    stop_frontend
    ;;
  restart)
    stop_frontend
    start_frontend
    ;;
  status)
    status
    ;;
  logs)
    show_logs
    ;;
  *)
    echo "用法: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac
