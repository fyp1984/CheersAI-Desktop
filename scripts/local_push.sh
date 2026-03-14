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
    log "=== 检查 Plugin Daemon 版本 (Docker Image) ==="

    # 1. 确定镜像标签 (使用 docker-compose.dev.yaml 中的版本或默认值)
    DOCKER_IMAGE="langgenius/dify-plugin-daemon:main-local"
    # 如果能从 docker-compose.dev.yaml 读取则更好，这里简化处理

    # 2. 检查本地 Docker 环境
    if ! command -v docker &> /dev/null; then
        log "⚠️ 本地未安装 Docker，无法提取 Plugin Daemon 二进制文件，跳过更新。"
        return
    fi

    LOCAL_CACHE_DIR="$SCRIPT_DIR/.cache/plugin_daemon"
    LOCAL_FILE="$LOCAL_CACHE_DIR/dify-plugin-daemon-server"
    mkdir -p "$LOCAL_CACHE_DIR"

    NEED_EXTRACT=true
    # 简单的缓存策略：如果文件存在且大小合理(>10MB)，则询问是否重新提取
    if [ -f "$LOCAL_FILE" ] && [ $(stat -f%z "$LOCAL_FILE" 2>/dev/null || stat -c%s "$LOCAL_FILE" 2>/dev/null) -gt 10000000 ]; then
        log "✅ 本地已存在 Plugin Daemon 缓存文件。"
        # 这里可以优化为检查镜像 ID，但为了简化，我们默认使用缓存，除非手动删除
        NEED_EXTRACT=false
    fi

    # 3. 从 Docker 镜像提取
    if [ "$NEED_EXTRACT" = true ]; then
        log "正在拉取镜像并提取二进制文件: $DOCKER_IMAGE (linux/amd64)"
        # 强制拉取 linux/amd64 架构，确保在服务器上可用
        if docker pull --platform linux/amd64 "$DOCKER_IMAGE"; then
            TEMP_ID=$(docker create --platform linux/amd64 "$DOCKER_IMAGE")
            if docker cp "$TEMP_ID:/app/main" "$LOCAL_FILE"; then
                log "✅ 提取成功。"
                chmod +x "$LOCAL_FILE"
            else
                log "❌ 提取失败。"
                docker rm -v "$TEMP_ID" >/dev/null
                return
            fi
            docker rm -v "$TEMP_ID" >/dev/null
        else
            log "❌ 镜像拉取失败，跳过更新。"
            return
        fi
    fi

    # 4. 上传到服务器
    log "正在上传 Plugin Daemon 到服务器..."
    # 上传并重命名为 dify-plugin-daemon
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
log "(仅同步 api/, web/, scripts/, README.md)"

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
    --exclude '*.log' \
    --exclude 'docker-compose*.yaml' \
    --include 'api/***' \
    --include 'web/***' \
    --include 'scripts/***' \
    --include 'README.md' \
    --exclude '*' \
    "$LOCAL_PATH/" "$SERVER_USER@$SERVER_IP:$SERVER_APP_DIR/"

log "✅ 代码同步完成"
log "请登录服务器执行构建脚本: ./scripts/server_build.sh"
