#!/bin/bash

# =========================================================================
# CheersAI Desktop 生产环境热部署脚本 (Hot Deploy)
# 功能：拉取最新代码(稀疏检出) -> 更新依赖 -> 数据库迁移 -> 前端构建 -> 重启服务
# 优化：
# 1. 使用 sparse-checkout 仅同步 api/ 和 web/ 目录，排除 docker/ 等无关文件
# 2. 增加 git 操作的详细进度日志
# 3. 前端构建性能优化：限制内存、禁用 SourceMap/ESLint/TypeCheck
# 用法：./server_deploy.sh [branch_name]
# =========================================================================

set -e  # 遇到错误立即退出

# 配置
APP_DIR="/home/cheersai/CheersAI-Desktop"
LOG_FILE="/home/cheersai/logs/deploy_$(date +%Y%m%d).log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 交互式确认：Git 分支
read -p "请输入要部署的 Git 分支 [默认: branch2B_v1.1]: " INPUT_BRANCH
BRANCH=${INPUT_BRANCH:-branch2B_v1.1}

log "=== 开始部署流程 (分支: $BRANCH) ==="

# 交互式确认：是否更新代码
read -p "是否需要从远程更新代码? (y/n) [默认: y]: " UPDATE_CODE
UPDATE_CODE=${UPDATE_CODE:-y}

if [[ "$UPDATE_CODE" =~ ^[Yy]$ ]]; then
    # 1. 代码更新 (使用稀疏检出优化)
    log "1. 配置稀疏检出并拉取代码..."

    # 确保目录存在
    if [ ! -d "$APP_DIR" ]; then
        mkdir -p "$APP_DIR"
    fi
    cd "$APP_DIR"

    # 如果是新目录，先初始化 Git
    if [ ! -d ".git" ]; then
        log "初始化 Git 仓库..."
        git init
        git remote add origin https://github.com/fyp1984/CheersAI-Desktop.git
    fi

    # 启用稀疏检出功能
    git config core.sparseCheckout true

    # 增加 Git 网络容错配置
    git config http.postBuffer 524288000
    git config http.lowSpeedLimit 0
    git config http.lowSpeedTime 999999
    # 尝试禁用 HTTP/2 避免 GnuTLS 错误
    git config http.version HTTP/1.1
    # 禁用 SSL 验证（仅用于临时解决证书问题，生产环境慎用）
    git config http.sslVerify false

    # 定义保留目录白名单 (排除 docker, docs, tests, scripts 等)
    # 只保留 api (后端), web (前端)
    # 注意：scripts 目录通常包含当前脚本本身，将其排除可能会导致脚本在 pull 后被删除
    # 如果脚本位于 APP_DIR/scripts 并且您正在 APP_DIR 下执行，git reset --hard 可能会影响正在运行的脚本
    # 建议将运维脚本放在独立目录（如 ~/scripts/）运行，与代码仓库解耦
   # 更新稀疏检出配置
cat > .git/info/sparse-checkout <<EOF
api/
web/
scripts/
docker-compose.dev.yaml
README.md
EOF

    # 尝试使用 SSH 协议作为备选 (如果 HTTPS 失败)
    # 需确保 ~/.ssh/id_ed25519.pub 已添加到 Github
    # git remote set-url origin git@github.com:fyp1984/CheersAI-Desktop.git

    log "正在从远程拉取分支: $BRANCH (显示详细进度)..."
    # 使用 --progress 显示进度
    # 增加重试机制 (Retry up to 3 times)
    MAX_RETRIES=3
    COUNT=0
    SUCCESS=0

    while [ $COUNT -lt $MAX_RETRIES ]; do
        # 尝试使用 HTTP/1.1 并增加 verbose 输出
        if git -c http.version=HTTP/1.1 fetch origin "$BRANCH" --progress --verbose 2>&1 | tee -a "$LOG_FILE"; then
            SUCCESS=1
            break
        else
            log "⚠️ 拉取失败，等待 5 秒后重试 ($((COUNT+1))/$MAX_RETRIES)..."
            # 第一次重试时尝试禁用 SSL 验证作为 fallback
            if [ $COUNT -eq 0 ]; then
                log "⚠️ 尝试临时禁用 SSL 验证..."
                git config http.sslVerify false
            fi
            sleep 5
            COUNT=$((COUNT+1))
        fi
    done

    if [ $SUCCESS -eq 0 ]; then
        log "❌ 多次尝试拉取代码失败，请检查网络或配置 SSH。"
        exit 1
    fi

    log "重置本地代码至最新状态..."
    # reset --hard 强制覆盖本地
    git reset --hard "origin/$BRANCH" 2>&1 | tee -a "$LOG_FILE"

else
    log "⏩ 跳过代码更新步骤，直接使用当前本地代码进行部署。"
    cd "$APP_DIR"
fi

# 2. 后端处理
log "2. 更新后端依赖..."
cd "$APP_DIR/api"

# 尝试加载 uv 环境变量 (应对非交互式 Shell 环境)
if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
elif [ -d "$HOME/.local/bin" ]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# 检查 uv 是否可用
if ! command -v uv &> /dev/null; then
    log "⚠️ 未找到 uv 命令，尝试自动安装..."

    # 尝试 1: 官方安装源 (GitHub/Astral)
    log "尝试从官方源安装 uv..."
    if curl -LsSf --connect-timeout 10 https://astral.sh/uv/install.sh | sh; then
        log "✅ uv 安装成功 (官方源)"
    else
        log "⚠️ 官方源连接超时，尝试使用 pip (清华源) 安装..."

        # 尝试 2: 使用 pip 安装 (指定清华镜像源)
        if command -v pip3 &> /dev/null; then
            pip3 install uv --user -i https://pypi.tuna.tsinghua.edu.cn/simple
            export PATH="$HOME/.local/bin:$PATH"

            if command -v uv &> /dev/null; then
                log "✅ uv 安装成功 (pip 清华源)"
            else
                log "❌ pip 安装完成但未找到 uv 命令，请检查 PATH 设置。"
                exit 1
            fi
        else
            log "❌ 无法安装 uv：官方源连接失败且未找到 pip3。"
            log "请手动安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
            exit 1
        fi
    fi

    # 加载环境
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    elif [ -d "$HOME/.local/bin" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi

if [ ! -d ".venv" ]; then
    log "创建虚拟环境..."
    uv venv .venv --python 3.12
fi
source .venv/bin/activate

log "2.1 优化 Python 依赖安装配置 (国内镜像加速)..."
# 优先使用清华源，配置阿里云作为备选
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
# 增加网络容错配置
export UV_HTTP_TIMEOUT=300  # 增加超时时间到 5分钟
export UV_CONCURRENT_DOWNLOADS=8 # 适当限制并发，防止拥塞

# 智能依赖检测
if [ -f "uv.lock" ] && [ -f ".uv.lock.deployed" ] && cmp -s "uv.lock" ".uv.lock.deployed"; then
    log "⏩ 后端依赖文件 (uv.lock) 未变更，跳过依赖同步..."
else
    log "📦 检测到依赖变更或首次部署，执行 uv sync..."
    uv sync 2>&1 | tee -a "$LOG_FILE"
    # 备份当前 lock 文件以供下次比对
    cp "uv.lock" ".uv.lock.deployed"
fi

log "3. 执行数据库迁移..."
export FLASK_APP=app.py

# 尝试加载环境变量 (兼容 .env 和 production.env)
# 1. 检查 API 的 .env
if [ ! -f "$APP_DIR/api/.env" ]; then
    log "⚠️ api/.env 不存在，尝试从 .env.example 复制..."
    if [ -f "$APP_DIR/api/.env.example" ]; then
        cp "$APP_DIR/api/.env.example" "$APP_DIR/api/.env"
        log "✅ 已创建 api/.env，请后续根据实际情况修改配置。"
    else
        log "❌ 未找到 api/.env.example，无法自动创建配置。"
    fi
fi

# 2. 检查 Web 的 .env
if [ ! -f "$APP_DIR/web/.env" ]; then
    log "⚠️ web/.env 不存在，尝试从 .env.example 复制..."
    if [ -f "$APP_DIR/web/.env.example" ]; then
        cp "$APP_DIR/web/.env.example" "$APP_DIR/web/.env"
        log "✅ 已创建 web/.env，请后续根据实际情况修改配置。"
    else
        log "❌ 未找到 web/.env.example，无法自动创建配置。"
    fi
fi

# 3. 加载环境变量 (优先加载 production.env，其次是 api/.env)
if [ -f "../config/production.env" ]; then
    log "加载生产环境配置..."
    set -a
    source "../config/production.env"
    set +a
elif [ -f "$APP_DIR/api/.env" ]; then
    log "加载 api/.env 配置..."
    set -a
    source "$APP_DIR/api/.env"
    set +a
fi

# 检查必要的数据库环境变量
if [ -z "$DB_PASSWORD" ]; then
    log "❌ 未检测到 DB_PASSWORD 环境变量，数据库连接将失败。"
    log "请确保 /home/cheersai/CheersAI-Desktop/config/production.env 文件存在且包含 DB_PASSWORD。"
    exit 1
fi

# === 新增：确保 Plugin Daemon 运行 ===
log "3.1 检查并启动 Plugin Daemon..."
if [ -f "../docker-compose.dev.yaml" ]; then
    COMPOSE_FILE="../docker-compose.dev.yaml"
elif [ -f "docker-compose.dev.yaml" ]; then
    COMPOSE_FILE="docker-compose.dev.yaml"
else
    COMPOSE_FILE=""
fi

if [ -n "$COMPOSE_FILE" ]; then
    if command -v docker >/dev/null 2>&1; then
        # Try to run docker ps to check permissions
        if ! docker ps >/dev/null 2>&1; then
             log "⚠️ 当前用户无法直接运行 Docker，尝试使用 sudo..."
             DOCKER_CMD="sudo docker"
             DOCKER_COMPOSE_CMD="sudo docker compose"

             # Fallback for older docker-compose
             if ! sudo docker compose version >/dev/null 2>&1; then
                 if command -v docker-compose >/dev/null 2>&1; then
                     DOCKER_COMPOSE_CMD="sudo docker-compose"
                 fi
             fi
        else
             DOCKER_CMD="docker"
             DOCKER_COMPOSE_CMD="docker compose"

             # Fallback for older docker-compose
             if ! $DOCKER_CMD compose version >/dev/null 2>&1; then
                 if command -v docker-compose >/dev/null 2>&1; then
                     DOCKER_COMPOSE_CMD="docker-compose"
                     if [[ "$DOCKER_CMD" == "sudo docker" ]]; then
                         DOCKER_COMPOSE_CMD="sudo docker-compose"
                     fi
                 fi
             fi
        fi

        # Check if plugin_daemon container is running
        PLUGIN_CONTAINER_NAME="dify-plugin-daemon"
        IS_RUNNING=false

        if $DOCKER_CMD ps --format '{{.Names}}' | grep -q "^${PLUGIN_CONTAINER_NAME}$"; then
             IS_RUNNING=true
        fi

        if [ "$IS_RUNNING" = true ]; then
            log "✅ Plugin Daemon (容器: $PLUGIN_CONTAINER_NAME) 正在运行。"
            read -p "是否重新部署/重启 Plugin Daemon? (y/N) [默认: N]: " REDEPLOY_PLUGIN
            REDEPLOY_PLUGIN=${REDEPLOY_PLUGIN:-n}

            if [[ "$REDEPLOY_PLUGIN" =~ ^[Yy]$ ]]; then
                 log "正在重新部署 Plugin Daemon..."
                 CMD="up -d --force-recreate plugin_daemon redis weaviate"
            else
                 log "⏩ 跳过 Plugin Daemon 部署。"
                 CMD=""
            fi
        else
            log "⚠️ Plugin Daemon 未运行，准备首次部署..."
            CMD="up -d plugin_daemon redis weaviate"
        fi

        if [ -n "$CMD" ]; then
             $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" $CMD 2>&1 | tee -a "$LOG_FILE"
        fi
    else
        log "⚠️ 未找到 docker 命令，跳过插件服务启动。"
    fi
else
    log "⚠️ 未找到 docker-compose.dev.yaml，无法自动启动插件服务。"
fi

uv run flask db upgrade 2>&1 | tee -a "$LOG_FILE"

# 3. 前端处理
log "4. 构建前端应用..."
cd "$APP_DIR/web"

# 检查 pnpm 是否可用
if ! command -v pnpm &> /dev/null; then
    log "⚠️ 未找到 pnpm 命令，尝试全局安装..."
    # 使用淘宝镜像加速安装 (需要 sudo 权限)
    if sudo npm install -g pnpm --registry=https://registry.npmmirror.com; then
        log "✅ pnpm 安装成功。"
    else
        log "❌ pnpm 安装失败 (EACCES)。请手动以 root 权限执行: sudo npm install -g pnpm"
        exit 1
    fi
fi

log "安装前端依赖 (pnpm 国内源加速)..."
# 配置淘宝镜像源
export NPM_CONFIG_REGISTRY="https://registry.npmmirror.com"

# === 关键修复：确保 basePath 环境变量在 build 之前注入 ===
export NEXT_PUBLIC_BASE_PATH="/cheersai_desktop"
export NEXT_PUBLIC_API_PREFIX="https://7smile.dlithink.com/cheersai_desktop/console/api"
export NEXT_PUBLIC_PUBLIC_API_PREFIX="https://7smile.dlithink.com/cheersai_desktop/api"

if [ -f "pnpm-lock.yaml" ] && [ -f ".pnpm-lock.yaml.deployed" ] && cmp -s "pnpm-lock.yaml" ".pnpm-lock.yaml.deployed"; then
    log "⏩ 前端依赖文件 (pnpm-lock.yaml) 未变更，跳过 pnpm install..."
else
    log "📦 检测到前端依赖变更，执行安装..."
    pnpm install 2>&1 | tee -a "$LOG_FILE"
    # 备份当前 lock 文件
    cp "pnpm-lock.yaml" ".pnpm-lock.yaml.deployed"
fi

log "编译前端代码 (显示详细进度)..."

# === 前端环境变量配置 (解决子路径部署 404/重定向问题) ===
# 必须与 Nginx 的 location /cheersai_desktop/ 对应
export NEXT_PUBLIC_BASE_PATH="/cheersai_desktop"
# 后端 API 地址 (通过 Nginx 反代)
export NEXT_PUBLIC_API_PREFIX="https://7smile.dlithink.com/cheersai_desktop/console/api"
export NEXT_PUBLIC_PUBLIC_API_PREFIX="https://7smile.dlithink.com/cheersai_desktop/api"

# === 性能优化关键配置 ===
# 1. 限制 Node.js 堆内存 (防止 OOM 崩溃，建议根据机器内存调整)
export NODE_OPTIONS="--max-old-space-size=4096"

# 2. 禁用 Source Map 生成 (节省大量内存和磁盘空间，生产环境通常不需要)
export GENERATE_SOURCEMAP=false
# Next.js 禁用 Source Map 的环境变量
export NEXT_PUBLIC_DISABLE_SOURCEMAPS=true

# 3. 禁用 ESLint 和 TypeScript 检查 (假设本地已通过，加快构建并省内存)
export NEXT_IGNORE_ESLINT=1
export NEXT_IGNORE_TYPECHECK=1

# 4. Next.js 遥测禁用
export NEXT_TELEMETRY_DISABLED=1

# 5. Turbopack 内存优化 (针对 Next.js 16+)
# 限制 Turbopack 的并发数，防止 CPU/内存爆表
export TURBOPACK_MEMORY_LIMIT=4096
# 如果可能，不使用 Turbopack 进行生产构建 (Next.js 默认可能使用 Webpack，但这里看到启用了 Turbopack)
# 可以尝试强制使用 Webpack 构建 (通常更稳定但稍慢)
# 或者通过参数限制并发

START_TIME=$(date +%s)
# 使用 pnpm run build
# 增加 --no-lint --no-mangling (如果支持) 等参数进一步降低负载
# 对于 Next.js，主要靠环境变量控制
# 尝试使用 taskset 限制 CPU 核心数 (例如只用 2 核)
if command -v taskset &> /dev/null; then
    log "限制构建使用 2 个 CPU 核心..."
    taskset -c 0,1 pnpm run build 2>&1 | tee -a "$LOG_FILE"
    BUILD_STATUS=$?
else
    pnpm run build 2>&1 | tee -a "$LOG_FILE"
    BUILD_STATUS=$?
fi

if [ $BUILD_STATUS -eq 0 ]; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log "✅ 前端构建完成，耗时: ${DURATION}秒"
else
    log "❌ 前端构建失败"
    exit 1
fi

# 4. 重启服务
log "5. 重启 Systemd 服务..."
# 需确保 cheersai 用户有 sudo 权限执行 systemctl
sudo systemctl restart cheersai-api
sudo systemctl restart cheersai-worker
sudo systemctl restart cheersai-web

# 5. 验证
log "6. 检查服务状态..."
sleep 5
if systemctl is-active --quiet cheersai-api && \
   systemctl is-active --quiet cheersai-web; then
    log "✅ 部署成功！所有服务运行正常。"

    # 显示最后几行日志作为摘要
    echo "--- 服务状态摘要 ---"
    systemctl status cheersai-api cheersai-web --no-pager | grep "Active:"
else
    log "❌ 部署可能存在问题，请检查 'systemctl status' 日志。"
    exit 1
fi

log "=== 部署结束 ==="
