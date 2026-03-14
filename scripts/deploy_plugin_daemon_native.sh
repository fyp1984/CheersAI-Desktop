#!/bin/bash

# =========================================================================
# Plugin Daemon 原生部署脚本 (非 Docker)
# 功能：下载二进制 -> 配置环境 -> 注册 Systemd 服务
# =========================================================================

set -e

APP_ROOT="/home/cheersai/CheersAI-Desktop"
API_ENV="$APP_ROOT/api/.env"
BIN_PATH="/usr/local/bin/dify-plugin-daemon"
SERVICE_FILE="/etc/systemd/system/dify-plugin-daemon.service"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
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
# 尝试使用本地系统 postgres 用户直接创建 (原生安装最常见的方式)
if command -v psql &> /dev/null; then
    log "尝试使用本地 postgres 用户免密创建..."
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw dify_plugin; then
        log "✅ 数据库 dify_plugin 已存在"
    else
        if sudo -u postgres psql -c "CREATE DATABASE dify_plugin;"; then
             log "✅ 数据库 dify_plugin 创建成功"
        else
             log "⚠️ 免密创建失败，尝试使用密码创建..."
             export PGPASSWORD=$DB_PASSWORD
             if ! psql -h $DB_HOST -p $DB_PORT -U postgres -lqt | cut -d \| -f 1 | grep -qw dify_plugin; then
                 psql -h $DB_HOST -p $DB_PORT -U postgres -c "CREATE DATABASE dify_plugin;"
             fi
        fi
    fi
else
    log "⚠️ 未找到 psql 命令，跳过数据库创建。请确保 'dify_plugin' 数据库已存在！"
fi

# 3. 安装二进制文件
log "3. 安装 Plugin Daemon 二进制文件..."
# 我们现在假设二进制文件已经通过 SCP 上传到了 APP_ROOT 目录下，名为 dify-plugin-daemon

if [ -f "$APP_ROOT/dify-plugin-daemon" ]; then
    log "找到本地上传的二进制文件..."
    sudo mv "$APP_ROOT/dify-plugin-daemon" "$BIN_PATH"
    sudo chmod +x "$BIN_PATH"
    log "✅ 二进制文件已安装到 $BIN_PATH"
elif [ -f "$BIN_PATH" ]; then
    log "✅ 二进制文件已存在: $BIN_PATH"
else
    error "未找到二进制文件！请确保已将 dify-plugin-daemon 上传到 $APP_ROOT"
    exit 1
fi

# 4. 创建 Systemd 服务
log "4. 配置 Systemd 服务..."

# 准备工作目录
WORK_DIR="$APP_ROOT/plugin_daemon"
mkdir -p "$WORK_DIR/storage"
sudo chown -R cheersai:cheersai "$WORK_DIR"

cat <<EOF | sudo tee "$SERVICE_FILE"
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

[Install]
WantedBy=multi-user.target
EOF

log "✅ Systemd 服务文件已创建: $SERVICE_FILE"

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
