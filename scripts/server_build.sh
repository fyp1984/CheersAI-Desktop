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

# 参数处理
FORCE_YES=false
if [[ "$1" == "-y" ]] || [[ "$1" == "--yes" ]]; then
    FORCE_YES=true
fi

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

# 3.1 检查 Plugin Daemon 部署
log "3.1 检查 Plugin Daemon 部署状态..."

# 检查是否有新上传的二进制文件，智能提示
if [ -f "$APP_DIR/dify-plugin-daemon" ]; then
    log "🌟 检测到新上传的 Plugin Daemon 二进制文件！"
    UPDATE_DEFAULT="Y"
    PROMPT_TEXT="是否立即部署/更新 Plugin Daemon? [Y/n] "
else
    UPDATE_DEFAULT="N"
    PROMPT_TEXT="是否重新配置/重启 Plugin Daemon? [y/N] "
fi

if [ "$FORCE_YES" = true ]; then
    log "⏩ 非交互模式：自动选择默认值 ($UPDATE_DEFAULT)"
    REPLY=$UPDATE_DEFAULT
else
    # 尝试检测是否为交互式终端，如果不是，则自动使用默认值
    if [ ! -t 0 ]; then
        log "⏩ 检测到非交互式环境：自动选择默认值 ($UPDATE_DEFAULT)"
        REPLY=$UPDATE_DEFAULT
    else
        echo ""
        log "=== Dify Plugin Daemon 管理 ==="
        read -p "$PROMPT_TEXT" -n 1 -r
        echo ""
    fi
fi

# 处理默认值
if [[ -z $REPLY ]]; then
    REPLY=$UPDATE_DEFAULT
fi

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "正在调用原生部署脚本..."
    if [ -f "$APP_DIR/scripts/deploy_plugin_daemon_native.sh" ]; then
        chmod +x "$APP_DIR/scripts/deploy_plugin_daemon_native.sh"
        if sudo "$APP_DIR/scripts/deploy_plugin_daemon_native.sh"; then
            log "✅ Plugin Daemon 部署/更新成功。"
        else
            log "❌ Plugin Daemon 部署失败。"
        fi
    else
        log "❌ 未找到部署脚本: $APP_DIR/scripts/deploy_plugin_daemon_native.sh"
    fi
else
    log "跳过 Plugin Daemon 独立部署流程。"
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

# 4. 重启服务与验证
log "5. 重启并验证所有服务..."
if [ -f "$APP_DIR/scripts/server_manage.sh" ]; then
    chmod +x "$APP_DIR/scripts/server_manage.sh"
    log "调用 server_manage.sh 进行统一重启..."

    # 尝试检查 sudo 是否可用（免密）
    if sudo -n true 2>/dev/null; then
        # sudo 可用，直接执行
        sudo "$APP_DIR/scripts/server_manage.sh" restart
        log "调用 server_manage.sh 进行统一状态检查..."
        sudo "$APP_DIR/scripts/server_manage.sh" status
        log "✅ 部署脚本执行完毕。"
    else
        # sudo 需要密码或不可用
        if [ ! -t 0 ]; then
            # 非交互式环境，跳过重启
            log "⚠️  检测到非交互式环境且 sudo 需要密码。"
            log "✅  构建已成功完成！"
            log "👉  请登录服务器并手动执行重启命令以应用更改："
            log "    sudo $APP_DIR/scripts/server_manage.sh restart"
            exit 0
        else
            # 交互式环境，正常执行（会提示输入密码）
            sudo "$APP_DIR/scripts/server_manage.sh" restart
            log "调用 server_manage.sh 进行统一状态检查..."
            sudo "$APP_DIR/scripts/server_manage.sh" status
            log "✅ 部署脚本执行完毕。"
        fi
    fi
else
    # 兼容旧逻辑
    log "未找到 server_manage.sh，执行基础重启..."
    # 同样检查 sudo
    if sudo -n true 2>/dev/null; then
        sudo systemctl restart cheersai-api cheersai-worker cheersai-web dify-plugin-daemon >> "$LOG_FILE" 2>&1 || true
    elif [ ! -t 0 ]; then
        log "⚠️  检测到非交互式环境且 sudo 需要密码，跳过重启。"
        log "👉  请手动执行：sudo systemctl restart cheersai-api cheersai-worker cheersai-web dify-plugin-daemon"
        exit 0
    else
        sudo systemctl restart cheersai-api cheersai-worker cheersai-web dify-plugin-daemon >> "$LOG_FILE" 2>&1 || true
    fi

    sleep 5
    if systemctl is-active --quiet cheersai-api && systemctl is-active --quiet cheersai-web && systemctl is-active --quiet dify-plugin-daemon; then
        log "✅ 部署成功！所有服务运行正常。"
        echo "--- 服务状态摘要 ---"
        systemctl status cheersai-api cheersai-web dify-plugin-daemon --no-pager | grep "Active:"
    else
        log "❌ 部署可能存在问题，请检查 'systemctl status' 日志。"
        exit 1
    fi
fi
