#!/bin/bash

# =========================================================================
# Plugin Daemon 原生部署脚本 (非 Docker)
# 功能：版本检测 -> 自动更新 -> 配置环境 -> 注册 Systemd 服务
# =========================================================================

set -e

APP_ROOT="/home/cheersai/CheersAI-Desktop"
API_ENV="$APP_ROOT/api/.env"
BIN_PATH="/usr/local/bin/dify-plugin-daemon"
VERSION_FILE="$APP_ROOT/plugin_daemon/version.txt"
SERVICE_FILE="/etc/systemd/system/dify-plugin-daemon.service"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN:${NC} $1"; }
error() { echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"; }

# 1. 获取配置信息
log "1. 读取配置信息..."
if [ ! -f "$API_ENV" ]; then
    error "未找到 api/.env 文件: $API_ENV"
    exit 1
fi

# 从 api/.env 读取 DB 密码和 Plugin Key
DB_PASSWORD=$(grep "^DB_PASSWORD=" "$API_ENV" | cut -d= -f2)
PLUGIN_KEY=$(grep "^PLUGIN_DAEMON_KEY=" "$API_ENV" | cut -d= -f2)
DB_HOST=$(grep "^DB_HOST=" "$API_ENV" | cut -d= -f2 | sed 's/localhost/127.0.0.1/') # 确保用 IP
DB_PORT=$(grep "^DB_PORT=" "$API_ENV" | cut -d= -f2)

if [ -z "$DB_PASSWORD" ] || [ -z "$PLUGIN_KEY" ]; then
    error "无法从 .env 获取 DB_PASSWORD 或 PLUGIN_DAEMON_KEY"
    exit 1
fi

log "数据库: $DB_HOST:$DB_PORT"
log "Plugin Key: ${PLUGIN_KEY:0:5}******"

# 2. 创建数据库
log "2. 检查并创建 dify_plugin 数据库..."
if command -v psql &> /dev/null; then
    # 尝试使用本地 postgres 用户免密创建
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw dify_plugin; then
        log "✅ 数据库 dify_plugin 已存在"
    else
        if sudo -u postgres psql -c "CREATE DATABASE dify_plugin;" 2>/dev/null; then
             log "✅ 数据库 dify_plugin 创建成功 (免密)"
        else
             log "⚠️ 免密创建失败，尝试使用密码创建..."
             export PGPASSWORD=$DB_PASSWORD
             if ! psql -h $DB_HOST -p $DB_PORT -U postgres -lqt | cut -d \| -f 1 | grep -qw dify_plugin; then
                 psql -h $DB_HOST -p $DB_PORT -U postgres -c "CREATE DATABASE dify_plugin;"
                 log "✅ 数据库 dify_plugin 创建成功 (密码)"
             fi
        fi
    fi
else
    warn "未找到 psql 命令，跳过数据库检查。"
fi

# 3. 版本检测与自动更新
log "3. 检查 Plugin Daemon 版本..."

# 获取最新版本 (优先尝试 GitHub API，超时则跳过)
LATEST_VERSION=""
CURRENT_VERSION=""

if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(cat "$VERSION_FILE")
    log "当前安装版本: $CURRENT_VERSION"
fi

log "正在检查 GitHub 最新版本..."
# 使用 curl 获取 latest release tag，设置 5 秒超时
LATEST_INFO=$(curl -s --max-time 10 https://api.github.com/repos/langgenius/dify-plugin-daemon/releases/latest || echo "")

if [ -n "$LATEST_INFO" ]; then
    LATEST_VERSION=$(echo "$LATEST_INFO" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    log "GitHub 最新版本: $LATEST_VERSION"
else
    warn "无法连接 GitHub API，跳过版本检测。"
fi

# 3.1 更新逻辑
NEED_UPDATE=false
if [ -n "$LATEST_VERSION" ]; then
    if [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
        log "发现新版本 ($CURRENT_VERSION -> $LATEST_VERSION)，准备更新..."
        NEED_UPDATE=true
    else
        log "当前已是最新版本。"
    fi
elif [ ! -f "$BIN_PATH" ]; then
    # 如果没有安装，即使没有获取到版本也要尝试安装（可能通过本地上传）
    NEED_UPDATE=true
    log "未检测到二进制文件，准备安装..."
fi

# 3.2 执行下载或安装
if [ "$NEED_UPDATE" = true ]; then
    DOWNLOAD_SUCCESS=false

    # 尝试从 GitHub 下载
    if [ -n "$LATEST_VERSION" ]; then
        DOWNLOAD_URL="https://github.com/langgenius/dify-plugin-daemon/releases/download/${LATEST_VERSION}/dify-plugin-linux-amd64"
        log "正在下载: $DOWNLOAD_URL"

        if curl -L --max-time 300 -o "$APP_ROOT/dify-plugin-daemon.new" "$DOWNLOAD_URL"; then
            if [ -s "$APP_ROOT/dify-plugin-daemon.new" ]; then
                log "✅ 下载成功"
                mv "$APP_ROOT/dify-plugin-daemon.new" "$APP_ROOT/dify-plugin-daemon"
                echo "$LATEST_VERSION" > "$VERSION_FILE"
                DOWNLOAD_SUCCESS=true
            else
                warn "下载文件为空"
                rm -f "$APP_ROOT/dify-plugin-daemon.new"
            fi
        else
            warn "下载失败 (超时或网络问题)"
        fi
    fi

    # 如果下载失败或未下载，检查是否有本地上传的文件
    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        if [ -f "$APP_ROOT/dify-plugin-daemon" ]; then
            log "发现本地上传的二进制文件，使用该文件进行安装..."
            DOWNLOAD_SUCCESS=true
            # 这种情况下我们无法确定版本，暂不更新 version.txt
        else
            if [ ! -f "$BIN_PATH" ]; then
                error "既无法下载更新，也未找到本地上传的文件！"
                exit 1
            else
                warn "更新失败，保留使用旧版本。"
            fi
        fi
    fi

    # 安装文件
    if [ "$DOWNLOAD_SUCCESS" = true ]; then
        log "安装二进制文件到 $BIN_PATH..."
        # 停止服务以允许覆盖
        sudo systemctl stop dify-plugin-daemon 2>/dev/null || true

        sudo mv "$APP_ROOT/dify-plugin-daemon" "$BIN_PATH"
        sudo chmod +x "$BIN_PATH"
        log "✅ 安装完成"
    fi
fi

# 4. 配置 Systemd 服务
log "4. 检查 Systemd 服务配置..."

# 准备工作目录
WORK_DIR="$APP_ROOT/plugin_daemon"
mkdir -p "$WORK_DIR/storage"
sudo chown -R cheersai:cheersai "$WORK_DIR"

# 始终重新生成服务文件，以防 .env 变更
cat <<EOF | sudo tee "$SERVICE_FILE" > /dev/null
[Unit]
Description=Dify Plugin Daemon Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=cheersai
Group=cheersai
WorkingDirectory=$WORK_DIR
ExecStart=$BIN_PATH
Restart=always
RestartSec=5

# 环境变量配置
Environment="DB_DSN=postgres://postgres:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/dify_plugin?sslmode=disable"
Environment="SERVER_KEY=${PLUGIN_KEY}"
Environment="MAX_PER_IP_RPS=100"
Environment="MAX_PER_IP_BURST=50"
Environment="LOG_LEVEL=info"
Environment="LISTEN_ADDRESS=0.0.0.0:5002"
Environment="PLUGIN_WORKING_PATH=$WORK_DIR/storage"
# 远程安装服务配置
Environment="PLUGIN_REMOTE_INSTALL_HOST=0.0.0.0"
Environment="PLUGIN_REMOTE_INSTALL_PORT=5003"

[Install]
WantedBy=multi-user.target
EOF

log "✅ Systemd 服务文件已更新"

# 5. 启动服务
log "5. 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable dify-plugin-daemon
sudo systemctl restart dify-plugin-daemon

sleep 3
if systemctl is-active --quiet dify-plugin-daemon; then
    log "✅ Plugin Daemon 启动成功！"
    systemctl status dify-plugin-daemon --no-pager
else
    error "启动失败，请查看日志: journalctl -u dify-plugin-daemon -xe"
    exit 1
fi
