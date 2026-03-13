#!/bin/bash

# =========================================================================
# Git 动态分支合并脚本 (Dynamic Branch Merge)
# 功能：
# 1. 将源分支 (Source) 合并到目标分支 (Target)
# 2. 支持通过命令行参数指定分支名称
# 3. 交互式冲突解决：逐个文件展示 diff，支持 ours/theirs/manual 选择
# 4. 自动推送与错误回滚
#
# 用法：./git_merge_dynamic.sh [source_branch] [target_branch]
# 示例：./git_merge_dynamic.sh master branch2B_v1.0
# =========================================================================

# 颜色配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数解析与默认值
SOURCE_BRANCH=${1:-"master"}
TARGET_BRANCH=${2:-"branch2B_v1.0"}

log() {
    echo -e "${GREEN}[Git-Merge]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[Warning]${NC} $1"
}

error() {
    echo -e "${RED}[Error]${NC} $1"
}

# 校验分支名称规范
validate_branch_name() {
    local branch_name=$1
    # 简单的正则校验：允许字母、数字、/、-、_、.
    if [[ ! "$branch_name" =~ ^[a-zA-Z0-9/\._-]+$ ]]; then
        error "分支名称 '$branch_name' 包含非法字符或格式不正确。"
        exit 1
    fi
}

validate_branch_name "$SOURCE_BRANCH"
validate_branch_name "$TARGET_BRANCH"

log "配置确认: 源分支=${BLUE}$SOURCE_BRANCH${NC} -> 目标分支=${BLUE}$TARGET_BRANCH${NC}"

# 1. 前置检查
log "检查当前 Git 状态..."
if [ -n "$(git status --porcelain)" ]; then
    error "工作区不干净，请先提交或暂存更改。"
    git status
    exit 1
fi

# 检查本地目标分支是否存在
if ! git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH"; then
    error "目标分支 '$TARGET_BRANCH' 在本地不存在，请先检出。"
    exit 1
fi

CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
    warn "当前不在目标分支 $TARGET_BRANCH 上 (当前: $CURRENT_BRANCH)"
    read -p "是否自动切换到 $TARGET_BRANCH ? (y/n) [y]: " SWITCH
    SWITCH=${SWITCH:-y}
    if [[ "$SWITCH" =~ ^[Yy]$ ]]; then
        git checkout "$TARGET_BRANCH"
    else
        error "操作已取消。"
        exit 1
    fi
fi

# 2. 获取最新代码
log "获取远程更新..."
git fetch origin

# 3. 开始合并
# 构造远程分支引用，通常是 origin/branch_name
REMOTE_SOURCE="origin/$SOURCE_BRANCH"

# 检查源分支是否存在于远程
if ! git rev-parse --verify "$REMOTE_SOURCE" >/dev/null 2>&1; then
    warn "远程分支 '$REMOTE_SOURCE' 不存在，尝试使用本地分支 '$SOURCE_BRANCH'..."
    if git show-ref --verify --quiet "refs/heads/$SOURCE_BRANCH"; then
        REMOTE_SOURCE="$SOURCE_BRANCH"
    else
        error "源分支 '$SOURCE_BRANCH' 在远程和本地均未找到。"
        exit 1
    fi
fi

log "尝试合并 $REMOTE_SOURCE 到当前分支..."
if git merge "$REMOTE_SOURCE"; then
    log "✅ 合并成功，无冲突。"
    # 自动推送
    read -p "是否推送到远程? (y/n) [y]: " PUSH
    PUSH=${PUSH:-y}
    if [[ "$PUSH" =~ ^[Yy]$ ]]; then
        git push origin "$TARGET_BRANCH"
        log "✅ 推送成功。"
    fi
    exit 0
else
    warn "⚠️ 检测到合并冲突！进入交互式解决模式..."
fi

# 4. 交互式解决冲突
CONFLICT_FILES=$(git diff --name-only --diff-filter=U)

if [ -z "$CONFLICT_FILES" ]; then
    error "合并失败但未检测到冲突文件？请检查 git status。"
    exit 1
fi

log "冲突文件列表:"
echo "$CONFLICT_FILES"
echo "--------------------------------------------------"

for file in $CONFLICT_FILES; do
    echo ""
    log "正在处理冲突文件: ${BLUE}$file${NC}"
    
    # 展示冲突内容 (使用 diff)
    echo -e "${YELLOW}--- 冲突内容预览 ---${NC}"
    # 尝试提取冲突区域的上下文
    grep -C 5 "^<<<<<<<" "$file" || echo "无法预览冲突区域 (可能是二进制文件)"
    echo -e "${YELLOW}--------------------${NC}"
    
    echo "请选择解决方案:"
    echo "  1) 保留当前分支版本 (ours/$TARGET_BRANCH) - 忽略源分支更改"
    echo "  2) 使用源分支版本 (theirs/$SOURCE_BRANCH) - 覆盖当前更改"
    echo "  3) 手动编辑 (将暂停脚本，编辑完成后继续)"
    echo "  4) 退出合并 (回滚所有操作)"
    
    while true; do
        read -p "请输入选项 [1-4]: " CHOICE
        case "$CHOICE" in
            1)
                git checkout --ours "$file"
                git add "$file"
                log "已选择: 保留当前版本"
                break
                ;;
            2)
                git checkout --theirs "$file"
                git add "$file"
                log "已选择: 使用源版本"
                break
                ;;
            3)
                log "脚本已暂停。请在另一个终端手动编辑文件: $file"
                log "编辑完成并保存后，请按回车键继续..."
                read -r
                git add "$file"
                log "已标记为解决"
                break
                ;;
            4)
                warn "正在回滚合并操作..."
                git merge --abort
                exit 1
                ;;
            *)
                echo "无效选项，请重试。"
                ;;
        esac
    done
done

# 5. 完成合并
echo ""
log "所有冲突已解决。"
if git commit --no-edit; then
    log "✅ 合并提交成功！"
    
    read -p "是否推送到远程? (y/n) [y]: " PUSH
    PUSH=${PUSH:-y}
    if [[ "$PUSH" =~ ^[Yy]$ ]]; then
        git push origin "$TARGET_BRANCH"
        log "✅ 推送成功。"
    fi
else
    error "提交失败，请手动检查 git status。"
    exit 1
fi
