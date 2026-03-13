#!/bin/bash

# =========================================================================
# CheersAI Desktop 自动化合并部署脚本 (Auto-Merge & Deploy)
# 版本: v2.0 (Git Flow Enhanced)
# 功能:
# 1. 自动切换/锁定到 branch2B_v1.0 分支
# 2. 强制合并远程 master 分支代码 (git merge --no-ff)
# 3. 执行依赖更新、数据库迁移、前端构建、服务重启
# 4. 包含完整的回滚机制和错误处理
# =========================================================================

set -e

# --- 1. 配置区域 (Configuration) ---
# 仓库与分支配置
REPO_URL="https://github.com/fyp1984/CheersAI-Desktop.git"
TARGET_BRANCH="branch2B_v1.0"
SOURCE_BRANCH="master"

# 路径配置
APP_DIR="/home/cheersai/CheersAI-Desktop"
LOG_DIR="/home/cheersai/logs"
LOG_FILE="${LOG_DIR}/deploy_$(date +%Y%m%d).log"

# Git 用户配置 (用于自动合并提交)
GIT_USER_NAME="CheersAI Deploy Bot"
GIT_USER_EMAIL="deploy@cheersai.cloud"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# --- 2. 辅助函数 ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 错误处理与回滚
error_exit() {
    log "❌ 部署失败: $1"
    if [ -n "$2" ] && [ "$2" != "HEAD" ]; then
        log "🔄 正在回滚 Git 状态到: $2"
        git reset --hard "$2" 2>&1 | tee -a "$LOG_FILE" || log "⚠️ 回滚命令执行失败"
    fi
    log "🚫 脚本异常退出 (Exit Code: 1)"
    exit 1
}

# --- 3. 环境初始化 ---
log "=== 开始部署流程 (Target: $TARGET_BRANCH) ==="
log "仓库地址: $REPO_URL"
log "部署目录: $APP_DIR"

if [ ! -d "$APP_DIR" ]; then
    log "创建部署目录..."
    mkdir -p "$APP_DIR"
fi

cd "$APP_DIR"

# 初始化 Git
if [ ! -d ".git" ]; then
    log "初始化 Git 仓库..."
    git init
    git remote add origin "$REPO_URL"
else
    # 幂等性：确保 origin 指向正确
    if ! git remote get-url origin >/dev/null 2>&1; then
        git remote add origin "$REPO_URL"
    else
        git remote set-url origin "$REPO_URL"
    fi
fi

# 配置 Git (本地有效)
git config user.name "$GIT_USER_NAME"
git config user.email "$GIT_USER_EMAIL"
git config core.sparseCheckout true
git config http.postBuffer 524288000
git config http.version HTTP/1.1

# 更新稀疏检出配置
cat > .git/info/sparse-checkout <<EOF
api/
web/
scripts/
README.md
EOF

# --- 4. Git 同步流程 (核心逻辑) ---
log ">>> [Phase 1] Git 代码同步与合并"

# 记录当前状态用于回滚 (如果不是空仓库)
if git rev-parse HEAD >/dev/null 2>&1; then
    PREV_HEAD_SHA=$(git rev-parse HEAD)
else
    PREV_HEAD_SHA=""
fi

# 4.1 拉取远程信息
log "Fetching origin..."
git fetch origin --progress 2>&1 | tee -a "$LOG_FILE" || error_exit "Git fetch 失败" "$PREV_HEAD_SHA"

# 4.2 切换到目标分支
log "检查并切换到分支: $TARGET_BRANCH"
if git show-ref --verify --quiet refs/heads/$TARGET_BRANCH; then
    # 本地已存在，直接切换
    git checkout $TARGET_BRANCH || error_exit "无法切换到本地分支 $TARGET_BRANCH" "$PREV_HEAD_SHA"
else
    # 本地不存在，尝试从远程检出
    if git show-ref --verify --quiet refs/remotes/origin/$TARGET_BRANCH; then
        git checkout -b $TARGET_BRANCH origin/$TARGET_BRANCH || error_exit "无法从远程检出 $TARGET_BRANCH" "$PREV_HEAD_SHA"
    else
        # 远程也不存在，基于 master 创建 (首次初始化场景)
        log "⚠️ 目标分支不存在，基于 origin/$SOURCE_BRANCH 创建新分支 $TARGET_BRANCH"
        git checkout -b $TARGET_BRANCH origin/$SOURCE_BRANCH || error_exit "无法基于源分支创建目标分支" "$PREV_HEAD_SHA"
    fi
fi

# 4.3 合并 Master 分支
log "正在将 origin/$SOURCE_BRANCH 合并入 $TARGET_BRANCH ..."
BEFORE_MERGE_SHA=$(git rev-parse HEAD)

# 执行合并：禁止快进，保留合并历史，遇到冲突自动停止
if git merge --no-ff "origin/$SOURCE_BRANCH" -m "Merge branch 'origin/$SOURCE_BRANCH' into $TARGET_BRANCH (Auto Deploy)"; then
    log "✅ Git 合并成功"
else
    log "❌ Git 合并冲突或失败"
    git merge --abort || true
    error_exit "合并操作因冲突被终止，请人工介入解决。" "$PREV_HEAD_SHA"
fi

# 4.4 变更审计
AFTER_MERGE_SHA=$(git rev-parse HEAD)
if [ "$BEFORE_MERGE_SHA" != "$AFTER_MERGE_SHA" ]; then
    log "📦 代码发生变更:"
    log "   Old SHA: $BEFORE_MERGE_SHA"
    log "   New SHA: $AFTER_MERGE_SHA"
    log "   变更文件统计:"
    git diff --stat "$BEFORE_MERGE_SHA" "$AFTER_MERGE_SHA" | tee -a "$LOG_FILE"
else
    log "⏩ 代码已是最新，无变更。"
fi

# --- 5. 后端依赖与迁移 ---
log ">>> [Phase 2] 后端处理 (Python/Flask)"
cd "$APP_DIR/api"

# 环境检查 (uv)
if [ -f "$HOME/.cargo/env" ]; then source "$HOME/.cargo/env"; fi
if [ -d "$HOME/.local/bin" ]; then export PATH="$HOME/.local/bin:$PATH"; fi

if ! command -v uv &> /dev/null; then
    log "⚠️ 未检测到 uv，尝试自动安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || error_exit "uv 安装失败" "$PREV_HEAD_SHA"
    source "$HOME/.cargo/env"
fi

# 虚拟环境
if [ ! -d ".venv" ]; then
    log "创建 Python 虚拟环境..."
    uv venv .venv --python 3.12
fi
source .venv/bin/activate

# 依赖配置优化
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
export UV_HTTP_TIMEOUT=300
export UV_CONCURRENT_DOWNLOADS=8

# 依赖同步
if [ -f "uv.lock" ] && [ -f ".uv.lock.deployed" ] && cmp -s "uv.lock" ".uv.lock.deployed"; then
    log "⏩ 后端依赖未变更，跳过同步"
else
    log "📦 同步后端依赖 (uv sync)..."
    uv sync 2>&1 | tee -a "$LOG_FILE" || error_exit "后端依赖安装失败" "$PREV_HEAD_SHA"
    cp "uv.lock" ".uv.lock.deployed"
fi

# 数据库迁移
log "执行数据库迁移..."
export FLASK_APP=app.py
# 加载环境变量
if [ -f "../config/production.env" ]; then
    export $(grep -v '^#' ../config/production.env | xargs)
elif [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DB_PASSWORD" ]; then
    error_exit "未找到 DB_PASSWORD 环境变量，请检查 production.env" "$PREV_HEAD_SHA"
fi

uv run flask db upgrade 2>&1 | tee -a "$LOG_FILE" || error_exit "数据库迁移失败" "$PREV_HEAD_SHA"

# --- 6. 前端构建 ---
log ">>> [Phase 3] 前端构建 (Next.js)"
cd "$APP_DIR/web"

# pnpm 检查
if ! command -v pnpm &> /dev/null; then
    log "安装 pnpm..."
    sudo npm install -g pnpm --registry=https://registry.npmmirror.com || error_exit "pnpm 安装失败" "$PREV_HEAD_SHA"
fi

export NPM_CONFIG_REGISTRY="https://registry.npmmirror.com"

# === 关键配置：环境变量注入 (修复 Logo/Manifest 路径) ===
export NEXT_PUBLIC_BASE_PATH="/cheersai_desktop"
export NEXT_PUBLIC_API_PREFIX="https://7smile.dlithink.com/cheersai_desktop/console/api"
export NEXT_PUBLIC_PUBLIC_API_PREFIX="https://7smile.dlithink.com/cheersai_desktop/api"

# 依赖安装
if [ -f "pnpm-lock.yaml" ] && [ -f ".pnpm-lock.yaml.deployed" ] && cmp -s "pnpm-lock.yaml" ".pnpm-lock.yaml.deployed"; then
    log "⏩ 前端依赖未变更，跳过安装"
else
    log "📦 安装前端依赖..."
    pnpm install 2>&1 | tee -a "$LOG_FILE" || error_exit "前端依赖安装失败" "$PREV_HEAD_SHA"
    cp "pnpm-lock.yaml" ".pnpm-lock.yaml.deployed"
fi

# 构建配置优化
export NODE_OPTIONS="--max-old-space-size=4096"
export GENERATE_SOURCEMAP=false
export NEXT_PUBLIC_DISABLE_SOURCEMAPS=true
export NEXT_IGNORE_ESLINT=1
export NEXT_IGNORE_TYPECHECK=1
export NEXT_TELEMETRY_DISABLED=1
export TURBOPACK_MEMORY_LIMIT=4096

log "开始编译前端代码..."
START_TIME=$(date +%s)

# 尝试使用 taskset 限制 CPU (避免服务器卡死)
BUILD_CMD="pnpm run build"
if command -v taskset &> /dev/null; then
    log "使用 taskset 限制 CPU 核心..."
    taskset -c 0,1 $BUILD_CMD 2>&1 | tee -a "$LOG_FILE"
else
    $BUILD_CMD 2>&1 | tee -a "$LOG_FILE"
fi

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    END_TIME=$(date +%s)
    log "✅ 前端构建成功 (耗时: $((END_TIME - START_TIME))s)"
else
    error_exit "前端构建失败" "$PREV_HEAD_SHA"
fi

# --- 7. 服务重启 ---
log ">>> [Phase 4] 重启服务"
# 确保有权限执行
if sudo systemctl restart cheersai-api cheersai-worker cheersai-web; then
    log "服务重启命令已发送"
else
    error_exit "服务重启失败 (systemctl error)" "$PREV_HEAD_SHA"
fi

# 健康检查
log "检查服务状态..."
sleep 5
if systemctl is-active --quiet cheersai-api && systemctl is-active --quiet cheersai-web; then
    log "✅ 所有服务运行正常 (Active)"
    systemctl status cheersai-api cheersai-web --no-pager | grep "Active:"
else
    error_exit "服务启动后状态检查失败" "$PREV_HEAD_SHA"
fi

log "=== 部署流程成功结束 ==="
exit 0
