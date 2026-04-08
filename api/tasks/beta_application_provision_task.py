import logging
from typing import Any

from celery import shared_task

from configs import dify_config
from extensions.ext_database import db
from extensions.ext_redis import redis_client
from libs.datetime_utils import naive_utc_now
from models.beta_application import BetaApplication
from models.beta_application_provision_task import BetaApplicationProvisionTask
from models.model import OperationLog
from services.beta_application_provisioning_service import (
    RETRY_MODE_FROM_FAILED,
    RETRY_MODE_FULL,
    BetaApplicationProvisionError,
    BetaApplicationProvisioningService,
)

logger = logging.getLogger(__name__)

BETA_PROVISION_TASK_QUEUE = "workflow"

ACTION_APPROVE = "approve"
ACTION_RETRY = "retry"
ACTION_PROVISION = "provision"
BETA_PROVISION_LOCK_KEY_TEMPLATE = "beta:provision:{application_id}"


def _record_operation(
    *,
    tenant_id: str | None,
    account_id: str | None,
    requested_ip: str | None,
    action: str,
    content: dict[str, Any],
):
    if not tenant_id or not account_id:
        return

    db.session.add(
        OperationLog(
            tenant_id=tenant_id,
            account_id=account_id,
            action=action,
            content=content,
            created_ip=(requested_ip or "unknown")[:255],
        )
    )
    db.session.commit()


def _mark_task_running(task: BetaApplicationProvisionTask):
    task.status = "running"
    task.error_message = None
    task.started_at = naive_utc_now()
    task.finished_at = None
    db.session.add(task)
    db.session.commit()


def _mark_task_finished(task: BetaApplicationProvisionTask):
    task.status = "success"
    task.error_message = None
    task.finished_at = naive_utc_now()
    db.session.add(task)
    db.session.commit()


def _mark_task_failed(task: BetaApplicationProvisionTask, error_message: str):
    task.status = "failed"
    task.error_message = (error_message or "unknown error")[:5000]
    task.finished_at = naive_utc_now()
    db.session.add(task)
    db.session.commit()


def _acquire_provision_lock(application_id: str):
    lock_key = BETA_PROVISION_LOCK_KEY_TEMPLATE.format(application_id=application_id)
    lock_timeout = max(30, int(dify_config.BETA_PROVISION_LOCK_TIMEOUT))
    lock = redis_client.lock(lock_key, timeout=lock_timeout, blocking=False)
    return lock if lock.acquire(blocking=False) else None, lock_key


def _release_provision_lock(lock: Any, lock_key: str):
    if lock is None:
        return
    try:
        lock.release()
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to release beta provision lock %s: %s", lock_key, exc)


@shared_task(queue=BETA_PROVISION_TASK_QUEUE)
def run_beta_application_provision_task(provision_task_id: str):
    task = (
        db.session.query(BetaApplicationProvisionTask)
        .filter(BetaApplicationProvisionTask.id == provision_task_id)
        .first()
    )
    if not task:
        logger.error("Beta provision task not found: %s", provision_task_id)
        return {"result": "fail", "message": "task not found"}

    service = BetaApplicationProvisioningService()
    application = db.session.query(BetaApplication).filter(BetaApplication.id == task.application_id).first()
    if not application:
        _mark_task_failed(task, "beta application not found")
        return {"result": "fail", "message": "beta application not found"}

    try:
        lock, lock_key = _acquire_provision_lock(task.application_id)
    except Exception as exc:
        db.session.rollback()
        error_message = f"failed to acquire distributed lock: {exc}"
        _mark_task_failed(task, error_message)
        _record_operation(
            tenant_id=task.requested_tenant_id,
            account_id=task.requested_by,
            requested_ip=task.requested_ip,
            action=f"beta_application.{task.action}.task.failed",
            content={
                "application_id": task.application_id,
                "provision_task_id": task.id,
                "celery_task_id": task.celery_task_id,
                "mode": task.mode,
                "error": error_message,
            },
        )
        return {"result": "fail", "message": error_message}

    if lock is None:
        error_message = "Another provisioning task is already running for this application."
        _mark_task_failed(task, error_message)
        _record_operation(
            tenant_id=task.requested_tenant_id,
            account_id=task.requested_by,
            requested_ip=task.requested_ip,
            action=f"beta_application.{task.action}.task.failed",
            content={
                "application_id": task.application_id,
                "provision_task_id": task.id,
                "celery_task_id": task.celery_task_id,
                "mode": task.mode,
                "error": error_message,
                "lock_key": lock_key,
            },
        )
        return {"result": "fail", "message": error_message}

    try:
        _mark_task_running(task)

        if task.action == ACTION_APPROVE:
            result = service.approve(application, reviewer_id=task.requested_by)
        elif task.action == ACTION_RETRY:
            result = service.retry(application, mode=task.mode or RETRY_MODE_FROM_FAILED)
        elif task.action == ACTION_PROVISION:
            result = service.provision(application, retry_mode=task.mode or RETRY_MODE_FULL)
        else:
            raise ValueError(f"Unsupported beta provision task action: {task.action}")

        _mark_task_finished(task)
        _record_operation(
            tenant_id=task.requested_tenant_id,
            account_id=task.requested_by,
            requested_ip=task.requested_ip,
            action=f"beta_application.{task.action}.task.success",
            content={
                "application_id": task.application_id,
                "provision_task_id": task.id,
                "celery_task_id": task.celery_task_id,
                "mode": task.mode,
            },
        )
        return {"result": "success", "application": result}
    except BetaApplicationProvisionError as exc:
        db.session.rollback()
        _mark_task_failed(task, exc.message)
        _record_operation(
            tenant_id=task.requested_tenant_id,
            account_id=task.requested_by,
            requested_ip=task.requested_ip,
            action=f"beta_application.{task.action}.task.failed",
            content={
                "application_id": task.application_id,
                "provision_task_id": task.id,
                "celery_task_id": task.celery_task_id,
                "mode": task.mode,
                "error": exc.message,
            },
        )
        return {"result": "fail", "message": exc.message}
    except Exception as exc:  # pragma: no cover
        db.session.rollback()
        error_message = str(exc)
        _mark_task_failed(task, error_message)
        _record_operation(
            tenant_id=task.requested_tenant_id,
            account_id=task.requested_by,
            requested_ip=task.requested_ip,
            action=f"beta_application.{task.action}.task.failed",
            content={
                "application_id": task.application_id,
                "provision_task_id": task.id,
                "celery_task_id": task.celery_task_id,
                "mode": task.mode,
                "error": error_message,
            },
        )
        logger.exception("Unexpected error while running beta provision task: %s", task.id)
        return {"result": "fail", "message": error_message}
    finally:
        _release_provision_lock(lock, lock_key)
