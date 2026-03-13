#!/bin/bash

# =========================================================================
# CheersAI 服务管理脚本
# 功能：一键启停、重启、查看状态，并输出详细的配置和环境信息
# 用法：./server_manage.sh [start|stop|restart|status]
# =========================================================================

# 配置路径
APP_ROOT="/home/cheersai/CheersAI-Desktop"
API_ENV="$APP_ROOT/api/.env"
WEB_ENV="$APP_ROOT/web/.env"
SERVICES="cheersai-api cheersai-worker cheersai-web"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

# 检查服务文件是否存在
check_service_files() {
    log "检查 Systemd 服务文件..."
    MISSING=0
    for svc in $SERVICES; do
        if [ ! -f "/etc/systemd/system/${svc}.service" ]; then
            warn "服务文件缺失: /etc/systemd/system/${svc}.service"
            MISSING=1
        fi
    done

    if [ $MISSING -eq 1 ]; then
        error "部分服务未注册，请先检查部署状态或执行 sudo systemctl daemon-reload"
    else
        log "服务文件检查通过。"
    fi
}

# 显示配置摘要
show_config_summary() {
    echo "--------------------------------------------------"
    echo -e "${YELLOW}配置信息摘要:${NC}"
    echo "应用根目录: $APP_ROOT"

    if [ -f "$API_ENV" ]; then
        echo -e "后端配置 ($API_ENV):"
        echo "  - DB_HOST: $(grep '^DB_HOST=' "$API_ENV" | cut -d= -f2)"
        echo "  - REDIS_HOST: $(grep '^REDIS_HOST=' "$API_ENV" | cut -d= -f2)"
        echo "  - CONSOLE_API_URL: $(grep '^CONSOLE_API_URL=' "$API_ENV" | cut -d= -f2)"
    else
        warn "后端配置文件缺失: $API_ENV"
    fi

    if [ -f "$WEB_ENV" ]; then
        echo -e "前端配置 ($WEB_ENV):"
        echo "  - NEXT_PUBLIC_API_PREFIX: $(grep '^NEXT_PUBLIC_API_PREFIX=' "$WEB_ENV" | cut -d= -f2)"
        echo "  - NEXT_PUBLIC_BASE_PATH: $(grep '^NEXT_PUBLIC_BASE_PATH=' "$WEB_ENV" | cut -d= -f2)"
    else
        warn "前端配置文件缺失: $WEB_ENV"
    fi
    echo "--------------------------------------------------"
}

ACTION=${1:-"status"}

case "$ACTION" in
    start)
        check_service_files
        log "正在启动服务: $SERVICES ..."
        if sudo systemctl start $SERVICES; then
            log "✅ 启动命令已发送。"
            sleep 2
            sudo systemctl is-active $SERVICES
        else
            error "启动失败，请检查 journalctl -xe"
            exit 1
        fi
        ;;

    stop)
        log "正在停止服务: $SERVICES ..."
        if sudo systemctl stop $SERVICES; then
            log "✅ 服务已停止。"
        else
            error "停止失败。"
            exit 1
        fi
        ;;

    restart)
        check_service_files
        show_config_summary
        log "正在重启服务: $SERVICES ..."
        if sudo systemctl restart $SERVICES; then
            log "✅ 重启命令已发送，等待服务就绪..."
            # 简单的健康检查等待
            for i in {1..5}; do
                echo -n "."
                sleep 1
            done
            echo ""

            # 检查状态
            if systemctl is-active --quiet cheersai-api && systemctl is-active --quiet cheersai-web; then
                log "✅ 所有服务重启成功并运行中。"
            else
                warn "部分服务可能未正常启动，请查看下方状态详情。"
            fi
        else
            error "重启失败。"
            exit 1
        fi
        ;;

    status)
        show_config_summary
        echo ""
        log "=== Systemd 服务状态 ==="
        sudo systemctl status $SERVICES --no-pager

        echo ""
        log "=== 端口监听状态 (TCP) ==="
        # 检查 8080 (API) 和 3000 (Web)
        sudo ss -tulpn | grep -E ':(8080|3000)' || echo "未检测到 8080 或 3000 端口监听"

        echo ""
        log "=== Nginx 代理状态 ==="
        if systemctl is-active --quiet nginx; then
            echo "Nginx: Running"
        else
            warn "Nginx: Stopped (Web 访问可能不可用)"
        fi
        ;;

    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
