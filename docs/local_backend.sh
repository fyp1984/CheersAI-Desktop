#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.dev.yaml"
API_LOG_DIR="${ROOT_DIR}/logs"
API_LOG_FILE="${API_LOG_DIR}/api-dev.log"
API_PID_FILE="${ROOT_DIR}/api/.flask_dev.pid"

ensure_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: 'uv' 命令不存在，请先安装 uv 并确保其在 PATH 中。" >&2
    exit 1
  fi
}

start_docker() {
  echo "[START] 启动 Docker 中间件 (postgres / redis / weaviate / plugin_daemon)..."
  docker compose -f "${COMPOSE_FILE}" up -d
  echo "[OK] Docker 中间件已启动。"
}

stop_docker() {
  echo "[STOP] 停止 Docker 中间件（保留数据卷）..."
  docker compose -f "${COMPOSE_FILE}" down || true
  echo "[OK] Docker 中间件已停止。"
}

start_api() {
  ensure_uv

  mkdir -p "${API_LOG_DIR}"

  if [[ -f "${API_PID_FILE}" ]]; then
    local pid
    pid="$(cat "${API_PID_FILE}" || true)"
    if [[ -n "${pid}" ]] && ps -p "${pid}" >/dev/null 2>&1; then
      echo "[INFO] API 已在运行，PID=${pid}。如需重启请先执行: $0 stop 或 $0 restart"
      return
    else
      rm -f "${API_PID_FILE}"
    fi
  fi

  echo "[START] 启动后端 API (uv run --project . flask run)..."
  cd "${ROOT_DIR}/api"
  nohup uv run --project . flask run --host 0.0.0.0 --port=5001 --debug \
    > "${API_LOG_FILE}" 2>&1 &
  local new_pid=$!
  echo "${new_pid}" > "${API_PID_FILE}"
  echo "[OK] API 已后台启动，PID=${new_pid}，日志: ${API_LOG_FILE}"
}

stop_api() {
  if [[ ! -f "${API_PID_FILE}" ]]; then
    echo "[INFO] 未找到 API PID 文件，可能 API 未运行。"
    return
  fi

  local pid
  pid="$(cat "${API_PID_FILE}" || true)"
  if [[ -z "${pid}" ]]; then
    echo "[WARN] PID 文件为空，删除并返回。"
    rm -f "${API_PID_FILE}"
    return
  fi

  if ps -p "${pid}" >/dev/null 2>&1; then
    echo "[STOP] 停止 API 进程，PID=${pid}..."
    kill "${pid}" || true
    sleep 2
    if ps -p "${pid}" >/dev/null 2>&1; then
      echo "[WARN] API 未正常退出，发送 SIGKILL..."
      kill -9 "${pid}" || true
    fi
  else
    echo "[INFO] PID=${pid} 的进程不存在，删除 PID 文件。"
  fi

  rm -f "${API_PID_FILE}"
  echo "[OK] API 已停止。"
}

status() {
  echo "== Docker 中间件状态 =="
  docker compose -f "${COMPOSE_FILE}" ps || true
  echo

  echo "== API 进程状态 =="
  if [[ -f "${API_PID_FILE}" ]]; then
    local pid
    pid="$(cat "${API_PID_FILE}" || true)"
    if [[ -n "${pid}" ]] && ps -p "${pid}" >/dev/null 2>&1; then
      echo "API 运行中，PID=${pid}"
    else
      echo "API 未运行（PID 文件存在但无对应进程），建议执行: $0 start 或手动删除 ${API_PID_FILE}"
    fi
  else
    echo "API 未运行（未找到 PID 文件）。"
  fi
}

show_logs() {
  if [[ ! -f "${API_LOG_FILE}" ]]; then
    echo "[INFO] 日志文件不存在: ${API_LOG_FILE}"
    return
  fi
  echo "[LOGS] tail -n 100 -f ${API_LOG_FILE}"
  tail -n 100 -f "${API_LOG_FILE}"
}

case "${1:-}" in
  start)
    start_docker
    start_api
    ;;
  stop)
    stop_api
    stop_docker
    ;;
  restart)
    stop_api
    stop_docker
    start_docker
    start_api
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
