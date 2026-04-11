"""
审计日志同步与清理任务
Audit Log Sync and Cleanup Tasks
"""

import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from configs import dify_config
from extensions.ext_database import db
from models.model import OperationLog

logger = logging.getLogger(__name__)


def sync_logs_to_nexus(tenant_id: str, max_retry: int = 3) -> dict:
    """
    同步审计日志到 Nexus

    Args:
        tenant_id: 租户ID
        max_retry: 最大重试次数

    Returns:
        同步结果统计
    """
    if not dify_config.NEXUS_AUDIT_SYNC_ENABLED:
        logger.info("[AUDIT SYNC] Nexus sync is disabled, skipping")
        return {"success": 0, "failed": 0, "skipped": 0, "disabled": True}

    if not dify_config.NEXUS_AUDIT_API_URL:
        logger.warning("[AUDIT SYNC] NEXUS_AUDIT_API_URL not configured, skipping")
        return {"success": 0, "failed": 0, "skipped": 0, "not_configured": True}

    result = {"success": 0, "failed": 0, "skipped": 0}

    with Session(db.engine) as session:
        pending_logs = (
            session.query(OperationLog)
            .filter(
                OperationLog.tenant_id == tenant_id,
                OperationLog.sync_status == "pending",
                or_(OperationLog.is_expired.is_(None), OperationLog.is_expired == False),
            )
            .limit(dify_config.NEXUS_AUDIT_SYNC_BATCH_SIZE)
            .all()
        )

        if not pending_logs:
            result["skipped"] = 0
            return result

        for log in pending_logs:
            try:
                synced = _do_sync_to_nexus(log, session)
                if synced:
                    log.sync_status = "synced"
                    log.sync_time = datetime.now()
                    result["success"] += 1
                else:
                    log.sync_status = "failed"
                    result["failed"] += 1
            except Exception:
                logger.exception("[AUDIT SYNC] 同步日志失败: %s", log.id)
                log.sync_status = "failed"
                result["failed"] += 1

        session.commit()

    logger.info(
        "[AUDIT SYNC] 同步完成: tenant=%s, success=%s, failed=%s", tenant_id, result["success"], result["failed"]
    )
    return result


def _do_sync_to_nexus(log: OperationLog, session: Session) -> bool:
    """
    执行实际的同步操作到 Nexus

    Returns:
        是否成功
    """
    if not dify_config.NEXUS_AUDIT_API_URL or not dify_config.NEXUS_AUDIT_SYNC_ENABLED:
        return False

    try:
        log_data = _transform_log_to_nexus_format(log)

        headers = {
            "Content-Type": "application/json",
        }
        if dify_config.NEXUS_AUDIT_API_KEY:
            headers["X-API-Key"] = dify_config.NEXUS_AUDIT_API_KEY

        timeout = httpx.Timeout(dify_config.NEXUS_AUDIT_SYNC_TIMEOUT, connect=10.0)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{dify_config.NEXUS_AUDIT_API_URL}/api/v1/audit-logs",
                json=log_data,
                headers=headers,
            )

            if response.status_code in (200, 201):
                logger.debug("[AUDIT SYNC] 成功同步日志: %s", log.id)
                return True
            else:
                logger.warning(
                    "[AUDIT SYNC] Nexus API 返回错误: status=%s, response=%s",
                    response.status_code,
                    response.text[:200],
                )
                return False

    except httpx.RequestError:
        logger.exception("[AUDIT SYNC] 网络请求失败: %s", log.id)
        raise
    except Exception:
        logger.exception("[AUDIT SYNC] 同步日志时发生未知错误: %s", log.id)
        raise


def _transform_log_to_nexus_format(log: OperationLog) -> dict:
    """
    将 Desktop 的 OperationLog 转换为 Nexus AuditLogDTO 格式

    Args:
        log: Desktop 操作日志

    Returns:
        Nexus 格式的审计日志数据
    """
    action_mapping = {
        "file_mask": "file_desensitize",
        "file_restore": "file_restore",
        "knowledge_sync": "knowledge_sync",
        "chat": "chat",
        "search": "search",
        "workflow": "workflow",
    }

    log_type = "user_action"
    if log.operation_type == "chat":
        log_type = "user_action"
    elif log.operation_type in ("desensitize", "restore"):
        log_type = "admin_action"
    else:
        log_type = "user_action"

    action = action_mapping.get(log.operation_type or log.action, log.action or "unknown")

    target_type = None
    target_id = None
    if log.content and isinstance(log.content, dict):
        target_type = log.content.get("resource_type")
        target_id = log.content.get("resource_id")

    return {
        "id": log.id,
        "logType": log_type,
        "action": action,
        "operatorId": log.account_id,
        "operatorName": log.account_name,
        "targetType": target_type,
        "targetId": target_id,
        "beforeData": None,
        "afterData": log.content,
        "ipAddress": log.created_ip,
        "userAgent": log.device_info,
        "result": "success" if log.error_message is None else "failure",
        "errorMessage": log.error_message,
    }


def cleanup_expired_logs(tenant_id: str, retention_days: int = 90) -> dict:
    """
    清理过期的审计日志

    Args:
        tenant_id: 租户ID
        retention_days: 保留天数

    Returns:
        清理结果统计
    """
    result = {"cleaned": 0}

    if retention_days <= 0:
        logger.info("[AUDIT CLEANUP] retention_days 为 0，跳过清理")
        return result

    cutoff_date = datetime.now() - timedelta(days=retention_days)

    with Session(db.engine) as session:
        expired_logs = (
            session.query(OperationLog)
            .filter(
                OperationLog.tenant_id == tenant_id,
                OperationLog.sync_status == "synced",
                OperationLog.created_at <= cutoff_date,
                or_(OperationLog.is_expired.is_(None), OperationLog.is_expired == False),
            )
            .all()
        )

        for log in expired_logs:
            log.is_expired = True

        result["cleaned"] = len(expired_logs)
        session.commit()

    logger.info("[AUDIT CLEANUP] 清理完成: tenant=%s, cleaned=%s", tenant_id, result["cleaned"])
    return result


def get_audit_retention_days(tenant_id: str) -> int:
    """
    获取审计日志保留天数

    根据日志类型使用不同的保留策略:
    - user_action (用户行为): 90天
    - admin_action (管理操作): 365天
    - system_event (系统事件): 30天
    - security_event (安全事件): 365天

    Args:
        tenant_id: 租户ID

    Returns:
        保留天数，默认 90 天
    """
    return 90
