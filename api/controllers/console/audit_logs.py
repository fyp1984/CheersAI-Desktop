"""
审计日志API - 从 Nexus 获取审计日志
Audit Logs API - Fetch from Nexus
"""

import logging
from datetime import datetime

import httpx
from flask import Blueprint, request
from werkzeug.exceptions import Forbidden

# 操作类型中英文映射
ACTION_DESCRIPTIONS = {
    "login": "用户登录",
    "logout": "用户登出",
    "file_upload": "文件上传",
    "file_mask": "文件脱敏",
    "file_delete": "文件删除",
    "file_download": "文件下载",
    "file_restore": "文件恢复",
    "create_dataset": "创建知识库",
    "knowledge_sync": "知识库同步",
    "knowledge_delete": "删除知识库",
    "member_invite": "成员邀请",
    "member_remove": "成员移除",
    "workflow": "工作流操作",
    "chat": "聊天完成",
    "search": "全局搜索",
}
from configs import dify_config
from controllers.console.wraps import account_initialization_required
from libs.desktop_auth import has_any_workspace_capability
from libs.login import current_account_with_tenant, login_required

logger = logging.getLogger(__name__)

audit_logs_bp = Blueprint("audit_logs", __name__, url_prefix="/console/api/audit-logs")


def _require_audit_view() -> None:
    current_user, current_tenant_id = current_account_with_tenant()
    if not has_any_workspace_capability(current_user, ["desktop_audit_view"], current_tenant_id):
        raise Forbidden()


def _fetch_from_nexus(params: dict) -> dict:
    """从 Nexus 获取审计日志"""
    if not dify_config.NEXUS_AUDIT_API_URL:
        logger.info("NEXUS_AUDIT_API_URL 未配置")
        return {"list": [], "total": 0}
    headers = {"Content-Type": "application/json"}
    if dify_config.NEXUS_AUDIT_API_KEY:
        headers["X-API-Key"] = dify_config.NEXUS_AUDIT_API_KEY
    try:
        timeout = httpx.Timeout(30.0, connect=10.0)
        with httpx.Client(timeout=timeout) as client:
            response = client.get(
                f"{dify_config.NEXUS_AUDIT_API_URL}/api/v1/audit-logs",
                params=params,
                headers=headers,
            )
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict):
                    data = result.get("data")
                    if isinstance(data, dict):
                        return data
                    return result
                return {"list": [], "total": 0}
            else:
                logger.warning("Nexus API 返回错误: status=%s, body=%s", response.status_code, response.text[:200])
                return {"list": [], "total": 0}
    except Exception:
        logger.exception("从 Nexus 获取审计日志失败")
        return {"list": [], "total": 0}


@audit_logs_bp.route("", methods=["GET"])
@login_required
@account_initialization_required
def get_audit_logs():
    """获取审计日志列表"""
    _require_audit_view()
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 10))
        params = {
            "page": page,
            "pageSize": page_size,
        }
        if request.args.get("logType"):
            params["logType"] = request.args.get("logType")
        if request.args.get("action"):
            params["action"] = request.args.get("action")
        if request.args.get("operatorName"):
            params["operatorName"] = request.args.get("operatorName")
        if request.args.get("ipAddress"):
            params["ipAddress"] = request.args.get("ipAddress")
        if request.args.get("result"):
            params["result"] = request.args.get("result")
        result = _fetch_from_nexus(params)
        logs = result.get("list", [])
        total = result.get("total", 0)
        formatted = []
        for log in logs:
            formatted.append(
                {
                    "id": log.get("id", ""),
                    "logType": log.get("logType", ""),
                    "logTypeDesc": log.get("logTypeDesc", ""),
                    "action": log.get("action", ""),
                    "actionDesc": log.get("actionDesc", ""),
                    "operatorId": log.get("operatorId", ""),
                    "operatorName": log.get("operatorName", ""),
                    "targetType": log.get("targetType", ""),
                    "targetId": log.get("targetId", ""),
                    "beforeData": log.get("beforeData"),
                    "afterData": log.get("afterData"),
                    "ipAddress": log.get("ipAddress", ""),
                    "userAgent": log.get("userAgent", ""),
                    "result": log.get("result", "success"),
                    "errorMessage": log.get("errorMessage", ""),
                    "createdAt": log.get("createdAt", ""),
                }
            )
        return {
            "data": formatted,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
    except Exception as e:
        logger.exception("获取审计日志失败")
        return {"error": str(e)}, 500


@audit_logs_bp.route("/stats", methods=["GET"])
@login_required
@account_initialization_required
def get_audit_stats():
    """获取审计日志统计"""
    _require_audit_view()
    try:
        total = 0
        for log_type in ["user_action", "admin_action", "security_event"]:
            params = {"logType": log_type, "pageSize": 1}
            result = _fetch_from_nexus(params)
            total += result.get("total", 0)
        return {
            "total": total,
            "today": 0,
        }
    except Exception as e:
        logger.exception("获取审计统计失败")
        return {"error": str(e)}, 500


@audit_logs_bp.route("/actions", methods=["GET"])
@login_required
@account_initialization_required
def get_audit_actions():
    """获取所有操作类型（从 Nexus 获取已知的操作类型）"""
    _require_audit_view()
    try:
        known_actions = [
            "login",
            "logout",
            "file_upload",
            "file_mask",
            "file_delete",
            "file_download",
            "file_restore",
            "create_dataset",
            "knowledge_sync",
            "knowledge_delete",
            "member_invite",
            "member_remove",
            "workflow",
            "chat",
            "search",
        ]
        return {"actions": known_actions}
    except Exception as e:
        return {"error": str(e)}, 500