#!/bin/bash

# ==============================================================================
# 脚本名称: git_merge_dynamic.sh
# 功能描述: 自动化Git分支合并工具，支持参数化调用和交互式向导。
#           包含分支检查、自动拉取、合并、冲突检测及推送功能。
# 使用场景: 用于日常开发分支向测试/主分支的合并操作，或CI/CD流程集成。
# 作者: CheersAI Dev Team
# 版本: v2.0.0
# 最后更新: 2026-03-13
# ==============================================================================

# 设置严格的错误处理模式
set -e

# 定义颜色代码，用于美化输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_SOURCE_BRANCH="master"
DEFAULT_TARGET_BRANCH="branch2B_v1.0"
INTERACTIVE_MODE=true

# 打印带时间戳的日志
log_info() {
    echo -e "${GREEN}[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[WARN] $(date '+%Y-%m-%d %H:%M:%S') $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1${NC}"
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}Git 动态合并脚本使用说明${NC}"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -b <分支名>   指定源分支 (默认为: $DEFAULT_SOURCE_BRANCH)"
    echo "  -t <分支名>   指定目标分支 (默认为: $DEFAULT_TARGET_BRANCH)"
    echo "  -m <消息>     指定合并提交消息 (可选)"
    echo "  -s            静默模式 (非交互模式，适用于CI/CD)"
    echo "  -h            显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0                                      # 交互式运行，使用默认分支"
    echo "  $0 -b feature-A -t develop              # 合并 feature-A 到 develop"
    echo "  $0 -s -b dev -t master -m 'Auto merge'  # 静默模式运行"
}

# 解析命令行参数
SOURCE_BRANCH=""
TARGET_BRANCH=""
COMMIT_MESSAGE=""

while getopts "b:t:m:sh" opt; do
    case $opt in
        b) SOURCE_BRANCH="$OPTARG" ;;
        t) TARGET_BRANCH="$OPTARG" ;;
        m) COMMIT_MESSAGE="$OPTARG" ;;
        s) INTERACTIVE_MODE=false ;;
        h) show_help; exit 0 ;;
        \?) log_error "无效选项: -$OPTARG"; show_help; exit 1 ;;
    esac
done

# 交互式输入逻辑
if [ "$INTERACTIVE_MODE" = true ]; then
    echo -e "${BLUE}=== 进入交互式配置模式 ===${NC}"

    # 确认源分支
    if [ -z "$SOURCE_BRANCH" ]; then
        read -p "请输入源分支名称 [默认: $DEFAULT_SOURCE_BRANCH]: " input_source
        SOURCE_BRANCH=${input_source:-$DEFAULT_SOURCE_BRANCH}
    fi

    # 确认目标分支
    if [ -z "$TARGET_BRANCH" ]; then
        read -p "请输入目标分支名称 [默认: $DEFAULT_TARGET_BRANCH]: " input_target
        TARGET_BRANCH=${input_target:-$DEFAULT_TARGET_BRANCH}
    fi

    # 确认提交消息（可选）
    if [ -z "$COMMIT_MESSAGE" ]; then
        read -p "请输入合并提交消息 (留空则使用默认消息): " input_msg
        COMMIT_MESSAGE="$input_msg"
    fi

    echo -e "${BLUE}=== 配置确认 ===${NC}"
    echo -e "源分支: ${YELLOW}$SOURCE_BRANCH${NC}"
    echo -e "目标分支: ${YELLOW}$TARGET_BRANCH${NC}"
    echo -e "提交消息: ${YELLOW}${COMMIT_MESSAGE:-<Git默认>}${NC}"
    echo
    read -p "确认执行合并操作? (y/n): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "用户取消操作，退出。"
        exit 0
    fi
else
    # 非交互模式下的默认值填充
    SOURCE_BRANCH=${SOURCE_BRANCH:-$DEFAULT_SOURCE_BRANCH}
    TARGET_BRANCH=${TARGET_BRANCH:-$DEFAULT_TARGET_BRANCH}
fi

# 核心逻辑开始
log_info "开始执行合并任务..."
log_info "源分支: $SOURCE_BRANCH -> 目标分支: $TARGET_BRANCH"

# 1. 检查工作区状态
if [ -n "$(git status --porcelain)" ]; then
    log_error "工作区有未提交的更改，请先提交或暂存后再运行此脚本。"
    git status
    exit 1
fi

# 2. 获取最新远程分支信息
log_info "正在从远程获取最新分支信息..."
git fetch origin

# 3. 验证分支是否存在
if ! git rev-parse --verify "origin/$SOURCE_BRANCH" >/dev/null 2>&1; then
    log_error "远程源分支 origin/$SOURCE_BRANCH 不存在！"
    exit 1
fi

if ! git rev-parse --verify "origin/$TARGET_BRANCH" >/dev/null 2>&1; then
    log_error "远程目标分支 origin/$TARGET_BRANCH 不存在！"
    exit 1
fi

# 4. 切换到目标分支并更新
log_info "切换到目标分支 $TARGET_BRANCH 并拉取最新代码..."
git checkout "$TARGET_BRANCH"
git pull origin "$TARGET_BRANCH"

# 5. 执行合并
log_info "正在将 $SOURCE_BRANCH 合并入 $TARGET_BRANCH ..."

# 构建合并命令
MERGE_CMD="git merge origin/$SOURCE_BRANCH"
if [ -n "$COMMIT_MESSAGE" ]; then
    MERGE_CMD="$MERGE_CMD -m \"$COMMIT_MESSAGE\""
fi

# 尝试合并
if $MERGE_CMD; then
    log_info "合并成功！"

    # 6. 推送更改
    log_info "正在推送到远程 $TARGET_BRANCH ..."
    git push origin "$TARGET_BRANCH"
    log_info "操作完成！所有更改已同步到远程仓库。"
else
    log_warn "合并过程中出现冲突！"

    if [ "$INTERACTIVE_MODE" = true ]; then
        echo -e "${YELLOW}检测到文件冲突。请手动解决冲突后继续。${NC}"
        echo "解决冲突的步骤:"
        echo "1. 打开冲突文件并修复内容。"
        echo "2. 使用 'git add <file>' 标记为已解决。"
        echo "3. 运行 'git commit' 完成合并提交。"
        echo "4. 运行 'git push origin $TARGET_BRANCH' 推送到远程。"

        read -p "是否现在打开Shell进行手动修复? (y/n): " resolve_now
        if [[ "$resolve_now" == "y" || "$resolve_now" == "Y" ]]; then
            echo -e "${BLUE}已暂停脚本，请在解决冲突后手动提交并推送。${NC}"
            exit 1
        else
            log_error "合并失败，请稍后手动解决冲突。"
            git merge --abort
            exit 1
        fi
    else
        log_error "静默模式下发生冲突，自动终止合并。请人工介入处理。"
        git merge --abort
        exit 1
    fi
fi

# 恢复到源分支（可选，根据工作流习惯，这里保持在目标分支可能更安全，或者询问用户）
if [ "$INTERACTIVE_MODE" = true ]; then
    read -p "是否切回源分支 $SOURCE_BRANCH ? (y/n): " switch_back
    if [[ "$switch_back" == "y" || "$switch_back" == "Y" ]]; then
        git checkout "$SOURCE_BRANCH"
        log_info "已切回 $SOURCE_BRANCH"
    fi
fi

log_info "脚本执行结束。"
