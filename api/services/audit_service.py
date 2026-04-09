"""
审计日志服务 - 数据库记录
Audit Log Service - Database Logging
"""

import logging
from typing import Any, Optional
from uuid import uuid4

from flask import request
from sqlalchemy.orm import Session

from extensions.ext_database import db
from models.model import OperationLog

logger = logging.getLogger(__name__)

OPERATION_TYPES = ["chat", "desensitize", "restore", "search", "workflow"]
SYNC_STATUSES = ["pending", "synced", "failed"]
DESENSITIZE_STATUSES = ["original", "desensitized"]


def desensitize_content(content: str) -> str:
    """
    脱敏处理 - 对敏感信息进行脱敏
    目前支持简单的正则匹配，后续可集成 NER 模型
    """
    if not content:
        return content

    import re

    content = re.sub(r"\b\d{11}\b", "***********", content)
    content = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "***@***.***", content)
    content = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "****-**-**", content)

    return content


def log_operation(
    action: str,
    content: Optional[dict[str, Any]] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    operation_type: Optional[str] = None,
    request_content: Optional[str] = None,
    response_content: Optional[str] = None,
    duration: Optional[int] = None,
    error_message: Optional[str] = None,
) -> Optional[str]:
    """
    记录操作日志到数据库

    Args:
        action: 操作类型，如 "file_mask", "file_restore", "knowledge_sync"
        content: 操作详情（JSON格式）
        resource_type: 资源类型，如 "file", "dataset"
        resource_id: 资源ID
        operation_type: 操作类型（chat/desensitize/restore/search/workflow）
        request_content: 请求内容（脱敏后存储）
        response_content: 响应内容
        duration: 执行耗时（毫秒）
        error_message: 错误信息

    Returns:
        日志ID，失败返回 None
    """
    from flask_login import current_user

    try:
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()
        if ip_address is None:
            ip_address = "unknown"

        device_info = request.headers.get("User-Agent", "")
        if len(device_info) > 255:
            device_info = device_info[:255]

        if request_content:
            request_content = desensitize_content(request_content)

        log_id = str(uuid4())
        tenant_id = getattr(current_user, "tenant_id", None) or getattr(current_user, "current_tenant_id", None)
        account_id = str(current_user.id) if current_user and hasattr(current_user, "id") else "unknown"
        account_name = current_user.name if current_user and hasattr(current_user, "name") else "unknown"

        log_entry = OperationLog(
            id=log_id,
            tenant_id=tenant_id,
            account_id=account_id,
            account_name=account_name,
            action=action,
            content=content or {},
            created_ip=ip_address,
            operation_type=operation_type,
            request_content=request_content,
            response_content=response_content,
            desensitize_status="desensitized" if request_content else "original",
            device_info=device_info,
            duration=duration,
            sync_status="pending",
            error_message=error_message,
        )

        with Session(db.engine, expire_on_commit=False) as session:
            session.add(log_entry)
            session.commit()

        logger.info("[AUDIT] ✓ 记录操作日志: %s, log_id: %s", action, log_id)
        return log_id

    except Exception as e:
        logger.error("[AUDIT] ✗ 记录操作日志失败: %s", e)
        return None


def write_log(
    tenant_id: str,
    account_id: str,
    account_name: str,
    action: str,
    operation_type: Optional[str] = None,
    content: Optional[dict[str, Any]] = None,
    request_content: Optional[str] = None,
    response_content: Optional[str] = None,
    created_ip: str = "unknown",
    device_info: Optional[str] = None,
    duration: Optional[int] = None,
    error_message: Optional[str] = None,
) -> Optional[str]:
    """
    直接写入操作日志（供异步任务调用）

    Args:
        tenant_id: 租户ID
        account_id: 账户ID
        account_name: 账户名
        action: 操作类型
        operation_type: 操作类型（chat/desensitize/restore/search/workflow）
        content: 操作详情
        request_content: 请求内容
        response_content: 响应内容
        created_ip: IP地址
        device_info: 设备信息
        duration: 执行耗时
        error_message: 错误信息

    Returns:
        日志ID
    """
    try:
        if request_content:
            request_content = desensitize_content(request_content)

        log_id = str(uuid4())

        log_entry = OperationLog(
            id=log_id,
            tenant_id=tenant_id,
            account_id=account_id,
            account_name=account_name,
            action=action,
            content=content or {},
            created_ip=created_ip,
            operation_type=operation_type,
            request_content=request_content,
            response_content=response_content,
            desensitize_status="desensitized" if request_content else "original",
            device_info=device_info,
            duration=duration,
            sync_status="pending",
            error_message=error_message,
        )

        with Session(db.engine, expire_on_commit=False) as session:
            session.add(log_entry)
            session.commit()

        logger.info("[AUDIT] ✓ 写入操作日志: %s, log_id: %s", action, log_id)
        return log_id

    except Exception as e:
        logger.error("[AUDIT] ✗ 写入操作日志失败: %s", e)
        return None
