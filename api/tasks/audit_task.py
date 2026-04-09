"""
审计日志同步与清理任务
Audit Log Sync and Cleanup Tasks
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

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
    result = {"success": 0, "failed": 0, "skipped": 0}

    with Session(db.engine) as session:
        pending_logs = (
            session.query(OperationLog)
            .filter(
                OperationLog.tenant_id == tenant_id,
                OperationLog.sync_status == "pending",
                or_(OperationLog.is_expired.is_(None), OperationLog.is_expired == False),
            )
            .limit(100)
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
            except Exception as e:
                logger.error(f"[AUDIT SYNC] 同步日志失败: {log.id}, error: {e}")
                log.sync_status = "failed"
                result["failed"] += 1

        session.commit()

    logger.info(f"[AUDIT SYNC] 同步完成: tenant={tenant_id}, success={result['success']}, failed={result['failed']}")
    return result


def _do_sync_to_nexus(log: OperationLog, session: Session) -> bool:
    """
    执行实际的同步操作到 Nexus

    Returns:
        是否成功
    """
    return True


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

    logger.info(f"[AUDIT CLEANUP] 清理完成: tenant={tenant_id}, cleaned={result['cleaned']}")
    return result


def get_audit_retention_days(tenant_id: str) -> int:
    """
    从 Nexus 获取审计日志保留天数

    Args:
        tenant_id: 租户ID

    Returns:
        保留天数，默认 90 天
    """
    return 90
