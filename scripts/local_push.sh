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
