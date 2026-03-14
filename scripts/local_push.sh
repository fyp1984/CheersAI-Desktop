#!/bin/bash

# =========================================================================
# CheersAI Desktop 本地推送部署脚本 (1/2: 代码同步)
# 功能：从本地同步代码到服务器
# 用法：./local_push.sh [local_project_path]
# =========================================================================

set -e

# 配置 - 服务器信息
SERVER_USER="cheersai"
SERVER_IP="62.234.210.100"
SERVER_APP_DIR="/home/cheersai/CheersAI-Desktop"

# 配置 - 本地默认路径
DEFAULT_LOCAL_PATH="/Users/FYP/Documents/WorkSpace/CheersAI/subproducts/CheersAI-Desktop/CheersAI-Desktop"
# 获取脚本所在目录，用于存放本地日志
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_LOG_FILE="$SCRIPT_DIR/deploy_push_$(date +%Y%m%d).log"

# 获取本地项目路径参数
LOCAL_PATH="${1:-$DEFAULT_LOCAL_PATH}"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOCAL_LOG_FILE"
}

# 检查本地路径是否存在
if [ ! -d "$LOCAL_PATH" ]; then
    log "❌ 错误：本地项目路径不存在: $LOCAL_PATH"
    exit 1
fi

# === 新增：Plugin Daemon 版本检测与上传 ===
check_and_upload_plugin_daemon() {
    log "=== 检查 Plugin Daemon 版本 ==="
    
    # 1. 获取 GitHub 最新版本
    LATEST_INFO=$(curl -s --max-time 10 https://api.github.com/repos/langgenius/dify-plugin-daemon/releases/latest || echo "")
    if [ -z "$LATEST_INFO" ]; then
        log "⚠️ 无法连接 GitHub API，跳过插件更新检查。"
        return
    fi
    
    LATEST_VERSION=$(echo "$LATEST_INFO" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    if [ -z "$LATEST_VERSION" ]; then
        log "⚠️ 无法解析版本号，跳过。"
        return
    fi
    
    log "GitHub 最新版本: $LATEST_VERSION"
    
    # 2. 检查本地是否有对应版本的缓存文件
    LOCAL_CACHE_DIR="$SCRIPT_DIR/.cache/plugin_daemon"
    LOCAL_FILE="$LOCAL_CACHE_DIR/dify-plugin-daemon-$LATEST_VERSION"
    mkdir -p "$LOCAL_CACHE_DIR"
    
    NEED_DOWNLOAD=false
    if [ ! -f "$LOCAL_FILE" ]; then
        NEED_DOWNLOAD=true
    else
        log "✅ 本地已存在该版本缓存。"
    fi
    
    # 3. 下载新版本
    if [ "$NEED_DOWNLOAD" = true ]; then
        DOWNLOAD_URL="https://github.com/langgenius/dify-plugin-daemon/releases/download/${LATEST_VERSION}/dify-plugin-linux-amd64"
        log "正在下载新版本: $DOWNLOAD_URL"
        if curl -L --max-time 300 -o "$LOCAL_FILE" "$DOWNLOAD_URL"; then
             log "✅ 下载完成。"
        else
             log "❌ 下载失败，跳过更新。"
             rm -f "$LOCAL_FILE"
             return
        fi
    fi
    
    # 4. 上传到服务器
    log "正在上传 Plugin Daemon 到服务器..."
    # 上传并重命名为 dify-plugin-daemon (去掉版本号后缀，方便部署脚本直接使用)
    if scp "$LOCAL_FILE" "$SERVER_USER@$SERVER_IP:$SERVER_APP_DIR/dify-plugin-daemon"; then
        log "✅ Plugin Daemon 上传成功。"
    else
        log "❌ 上传失败。"
    fi
}

# 执行插件检查 (不阻塞主流程)
check_and_upload_plugin_daemon

log "=== 开始部署流程 1/2: 本地代码推送 ==="
log "本地路径: $LOCAL_PATH"
log "目标服务器: $SERVER_USER@$SERVER_IP:$SERVER_APP_DIR"

# 1. 代码同步 (本地 -> 服务器)
log "正在同步代码到服务器..."
log "(仅同步 api/, web/, scripts/, docker-compose.dev.yaml, README.md)"

# 使用 rsync 进行增量同步
rsync -az --delete \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude 'dist' \
    --exclude '.DS_Store' \
    --exclude '.env' \
    --exclude 'uv.lock' \
    --exclude 'pnpm-lock.yaml' \
    --include 'api/***' \
    --include 'web/***' \
    --include 'scripts/***' \
    --include 'docker-compose.dev.yaml' \
    --include 'README.md' \
    --exclude '*' \
    "$LOCAL_PATH/" "$SERVER_USER@$SERVER_IP:$SERVER_APP_DIR/"

log "✅ 代码同步完成"
log "请登录服务器执行构建脚本: ./scripts/server_build.sh"
