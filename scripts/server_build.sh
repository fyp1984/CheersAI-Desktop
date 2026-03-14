#!/bin/bash

# =========================================================================
# CheersAI Desktop 服务器构建脚本 (2/2: 构建与重启)
# 功能：更新依赖 -> 数据库迁移 -> 前端构建 -> 重启服务
# 用法：./server_build.sh
# =========================================================================

set -e

APP_DIR="/home/cheersai/CheersAI-Desktop"
LOG_FILE="/home/cheersai/logs/deploy_$(date +%Y%m%d).log"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 仅记录到文件不输出到控制台的函数
log_file_only() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== 开始部署流程 2/2: 服务器端构建 ==="
log "详细日志将写入: $LOG_FILE"

# 2. 后端处理
log "2. 更新后端依赖..."
cd "$APP_DIR/api"

# 尝试加载 uv 环境变量
if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
elif [ -d "$HOME/.local/bin" ]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# 检查 uv
if ! command -v uv &> /dev/null; then
     log "⚠️ 未找到 uv 命令，请先手动安装 uv。"
     exit 1
fi

if [ ! -d ".venv" ]; then
    log "创建虚拟环境..."
    uv venv .venv --python 3.12 >> "$LOG_FILE" 2>&1
fi
source .venv/bin/activate

log "2.1 优化 Python 依赖安装配置..."
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
export UV_HTTP_TIMEOUT=300
export UV_CONCURRENT_DOWNLOADS=8

# 智能依赖检测
log "📦 执行 uv sync (详细日志见文件)..."
uv sync >> "$LOG_FILE" 2>&1

log "3. 执行数据库迁移..."
export FLASK_APP=app.py

# 环境变量处理
if [ ! -f "$APP_DIR/api/.env" ] && [ -f "$APP_DIR/api/.env.example" ]; then
    cp "$APP_DIR/api/.env.example" "$APP_DIR/api/.env"
fi
if [ ! -f "$APP_DIR/web/.env" ] && [ -f "$APP_DIR/web/.env.example" ]; then
    cp "$APP_DIR/web/.env.example" "$APP_DIR/web/.env"
fi

# 加载环境变量
if [ -f "../config/production.env" ]; then
    log_file_only "加载生产环境配置..."
    set -a; source "../config/production.env"; set +a
elif [ -f "$APP_DIR/api/.env" ]; then
    log_file_only "加载 api/.env 配置..."
    set -a; source "$APP_DIR/api/.env"; set +a
fi

if [ -z "$DB_PASSWORD" ]; then
    log "❌ 未检测到 DB_PASSWORD 环境变量。"
    exit 1
fi

# 3.1 检查并启动 Plugin Daemon
log "3.1 检查并启动 Plugin Daemon..."
if [ -f "../docker-compose.dev.yaml" ]; then COMPOSE_FILE="../docker-compose.dev.yaml";
elif [ -f "docker-compose.dev.yaml" ]; then COMPOSE_FILE="docker-compose.dev.yaml"; else COMPOSE_FILE=""; fi

if [ -n "$COMPOSE_FILE" ] && command -v docker >/dev/null 2>&1; then
        if ! docker ps >/dev/null 2>&1; then
             DOCKER_CMD="sudo docker"; DOCKER_COMPOSE_CMD="sudo docker compose"
             if ! sudo docker compose version >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then DOCKER_COMPOSE_CMD="sudo docker-compose"; fi
        else
             DOCKER_CMD="docker"; DOCKER_COMPOSE_CMD="docker compose"
             if ! docker compose version >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
                DOCKER_COMPOSE_CMD="docker-compose"
                if [[ "$DOCKER_CMD" == "sudo docker" ]]; then DOCKER_COMPOSE_CMD="sudo docker-compose"; fi
             fi
        fi

        PLUGIN_CONTAINER_NAME="dify-plugin-daemon"
        if ! $DOCKER_CMD ps --format '{{.Names}}' | grep -q "^${PLUGIN_CONTAINER_NAME}$"; then
            log "⚠️ Plugin Daemon 未运行。由于权限限制，请手动在服务器执行 'sudo docker compose up -d' 启动相关服务。"
        else
            log "✅ Plugin Daemon 正在运行。"
        fi
    fi

    uv run flask db upgrade >> "$LOG_FILE" 2>&1

# 3. 前端处理
log "4. 构建前端应用..."
cd "$APP_DIR/web"

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
    log "⚠️ 未找到 pnpm 命令，尝试全局安装..."
    sudo npm install -g pnpm --registry=https://registry.npmmirror.com >> "$LOG_FILE" 2>&1
fi

log "安装前端依赖 (pnpm 国内源加速)..."
export NPM_CONFIG_REGISTRY="https://registry.npmmirror.com"
export NEXT_PUBLIC_BASE_PATH="/cheersai_desktop"
export NEXT_PUBLIC_API_PREFIX="https://7smile.dlithink.com/cheersai_desktop/console/api"
export NEXT_PUBLIC_PUBLIC_API_PREFIX="https://7smile.dlithink.com/cheersai_desktop/api"

log "📦 执行 pnpm install (详细日志见文件)..."
pnpm install >> "$LOG_FILE" 2>&1

log "编译前端代码 (详细日志见文件)..."
export NODE_OPTIONS="--max-old-space-size=4096"
export GENERATE_SOURCEMAP=false
export NEXT_PUBLIC_DISABLE_SOURCEMAPS=true
export NEXT_IGNORE_ESLINT=1
export NEXT_IGNORE_TYPECHECK=1
export NEXT_TELEMETRY_DISABLED=1
export TURBOPACK_MEMORY_LIMIT=4096

START_TIME=$(date +%s)

# === 资源限制策略 ===
# 限制构建使用 2 个 CPU 核心
if command -v taskset &> /dev/null; then
    log "限制构建使用 2 个 CPU 核心..."
    taskset -c 0,1 pnpm run build >> "$LOG_FILE" 2>&1
    BUILD_STATUS=$?
else
    pnpm run build >> "$LOG_FILE" 2>&1
    BUILD_STATUS=$?
fi

if [ $BUILD_STATUS -eq 0 ]; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log "✅ 前端构建完成，耗时: ${DURATION}秒"
else
    log "❌ 前端构建失败，请检查日志: $LOG_FILE"
    exit 1
fi

# 4. 重启服务
log "5. 重启 Systemd 服务..."
sudo systemctl restart cheersai-api >> "$LOG_FILE" 2>&1
sudo systemctl restart cheersai-worker >> "$LOG_FILE" 2>&1
sudo systemctl restart cheersai-web >> "$LOG_FILE" 2>&1

# 5. 验证
log "6. 检查服务状态..."
sleep 5
if systemctl is-active --quiet cheersai-api && systemctl is-active --quiet cheersai-web; then
    log "✅ 部署成功！所有服务运行正常。"
    echo "--- 服务状态摘要 ---"
    systemctl status cheersai-api cheersai-web --no-pager | grep "Active:"
else
    log "❌ 部署可能存在问题，请检查 'systemctl status' 日志。"
    exit 1
fi
