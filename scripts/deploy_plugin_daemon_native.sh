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

# 读取 Redis 配置
REDIS_HOST=$(grep "^REDIS_HOST=" "$API_ENV" | cut -d= -f2 | sed 's/localhost/127.0.0.1/')
REDIS_PORT=$(grep "^REDIS_PORT=" "$API_ENV" | cut -d= -f2)
REDIS_PASSWORD=$(grep "^REDIS_PASSWORD=" "$API_ENV" | cut -d= -f2)
REDIS_DB=$(grep "^REDIS_DB=" "$API_ENV" | cut -d= -f2)

# 设置默认值
REDIS_HOST=${REDIS_HOST:-127.0.0.1}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_DB=${REDIS_DB:-0}

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

    # 确保 dify_plugin 用户存在并有权限
    log "配置数据库用户权限..."
    sudo -u postgres psql -c "CREATE USER dify_plugin WITH PASSWORD 'dify_plugin_password';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dify_plugin TO dify_plugin;" 2>/dev/null || true
    sudo -u postgres psql -d dify_plugin -c "GRANT ALL ON SCHEMA public TO dify_plugin;" 2>/dev/null || true
else
    warn "未找到 psql 命令，跳过数据库检查。"
fi

# 3. 版本检测与更新
log "3. 检查 Plugin Daemon 更新..."

# 说明：由于 Plugin Daemon 服务端二进制无法直接从 GitHub 下载（Release 中仅有 CLI 工具），
# 因此必须通过 local_push.sh 从本地 Docker 镜像提取并上传到服务器。

NEED_UPDATE=false

# 检查是否有新上传的二进制文件
if [ -f "$APP_ROOT/dify-plugin-daemon" ]; then
    log "发现新上传的二进制文件: $APP_ROOT/dify-plugin-daemon"
    NEED_UPDATE=true
elif [ ! -f "$BIN_PATH" ]; then
    error "未找到已安装的二进制文件，且未发现新上传的文件！请先通过 local_push.sh 上传。"
    exit 1
else
    log "未发现新上传的文件，保持当前版本。"
fi

# 执行安装
if [ "$NEED_UPDATE" = true ]; then
    log "安装二进制文件到 $BIN_PATH..."

    # 停止服务以允许覆盖
    sudo systemctl stop dify-plugin-daemon 2>/dev/null || true

    sudo mv "$APP_ROOT/dify-plugin-daemon" "$BIN_PATH"
    sudo chmod +x "$BIN_PATH"
    log "✅ 安装完成"

    # 更新版本记录 (这里简单记录日期作为版本)
    date +%Y%m%d_%H%M%S > "$VERSION_FILE"
fi

# 3.5 修复系统级 uv 路径依赖
log "修复 Dify Plugin Daemon 的 Python 依赖..."

# 创建 uv wrapper 以强制设置环境变量 (解决 Daemon 可能不透传 Env 导致 UV_VENV_CLEAR 失效的问题)
cat <<EOF > /tmp/uv_wrapper.sh
#!/bin/sh
export UV_VENV_CLEAR=1
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
export UV_HTTP_TIMEOUT=300
export UV_CONCURRENT_DOWNLOADS=4
# 尝试执行用户的 uv，如果不存在则尝试 python 模块的 uv
if [ -x "/home/cheersai/.local/bin/uv" ]; then
    exec /home/cheersai/.local/bin/uv "\$@"
elif command -v python3 >/dev/null; then
    # 尝试找到 python 模块里的 uv
    REAL_UV=\$(python3 -c 'from uv._find_uv import find_uv_bin; print(find_uv_bin())' 2>/dev/null)
    if [ -x "\$REAL_UV" ] && [ "\$REAL_UV" != "/usr/local/bin/uv" ]; then
        exec "\$REAL_UV" "\$@"
    fi
fi
# Fallback
echo "Error: Could not find real uv binary" >&2
exit 1
EOF

log "部署 uv wrapper 到 /usr/local/bin/uv..."
sudo mv /tmp/uv_wrapper.sh /usr/local/bin/uv
sudo chmod +x /usr/local/bin/uv

# 确保 python3 uv 模块也安装 (用于 Daemon 启动时的路径发现)
if command -v python3 &> /dev/null; then
    if ! python3 -c 'from uv._find_uv import find_uv_bin' 2>/dev/null; then
        log "正在为系统 python3 安装 uv 模块..."
        # 考虑到 Ubuntu 22.04+ 的 PEP 668 限制，强制安装或使用 pip3
        if command -v pip3 &> /dev/null; then
            sudo pip3 install uv --break-system-packages || sudo pip3 install uv
        else
            sudo apt-get update && sudo apt-get install -y python3-pip
            sudo pip3 install uv --break-system-packages || sudo pip3 install uv
        fi
        log "✅ uv 模块安装完成"
    else
        log "✅ python3 uv 模块已就绪"
    fi
else
    warn "未找到 python3，Plugin Daemon 可能无法正常运行 Python 插件！"
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
Environment="HOME=/home/cheersai"
Environment="UV_CACHE_DIR=/home/cheersai/.cache/uv"
# 配置 uv 使用国内镜像源 (清华源) 并增加超时限制
Environment="UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
Environment="UV_HTTP_TIMEOUT=300"
Environment="UV_CONCURRENT_DOWNLOADS=8"
# 关键修复：允许 uv 自动清理已存在的虚拟环境，避免交互式确认导致超时
Environment="UV_VENV_CLEAR=1"
Environment="PATH=/home/cheersai/.local/bin:/home/cheersai/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="DIFY_INNER_API_URL=http://127.0.0.1:5001/console/api"
Environment="DIFY_INNER_API_KEY=${PLUGIN_KEY}"
Environment="SERVER_KEY=${PLUGIN_KEY}"
Environment="PLATFORM=local"
Environment="DB_USERNAME=dify_plugin"
Environment="DB_PASSWORD=dify_plugin_password"
Environment="DB_HOST=${DB_HOST}"
Environment="DB_PORT=${DB_PORT}"
Environment="DB_DATABASE=dify_plugin"
Environment="REDIS_HOST=${REDIS_HOST}"
Environment="REDIS_PORT=${REDIS_PORT}"
Environment="REDIS_PASSWORD=${REDIS_PASSWORD}"
Environment="REDIS_DB=${REDIS_DB}"
Environment="MAX_PER_IP_RPS=100"
Environment="MAX_PER_IP_BURST=50"
Environment="LOG_LEVEL=info"
Environment="LISTEN_ADDRESS=0.0.0.0:5002"
Environment="PLUGIN_WORKING_PATH=$WORK_DIR/storage"
# 远程安装服务配置
Environment="PLUGIN_REMOTE_INSTALLING_HOST=0.0.0.0"
Environment="PLUGIN_REMOTE_INSTALLING_PORT=5003"

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
