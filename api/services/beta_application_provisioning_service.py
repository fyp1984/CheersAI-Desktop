import base64
import hashlib
import json
import logging
import re
import secrets
import string
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import requests
import urllib3

from configs import dify_config
from extensions.ext_database import db
from libs.datetime_utils import naive_utc_now
from models.beta_application import BetaApplication
from models.beta_application_notification import BetaApplicationNotification
from models.beta_application_provision_task import BetaApplicationProvisionTask
from models.beta_application_step import BetaApplicationStep
from services.beta_application_notification_service import BetaApplicationNotificationService

logger = logging.getLogger(__name__)

BETA_APPLICATION_STATUS_PENDING = "pending"
BETA_APPLICATION_STATUS_PROVISIONING = "provisioning"
BETA_APPLICATION_STATUS_SUCCESS = "success"
BETA_APPLICATION_STATUS_FAILED = "failed"
BETA_APPLICATION_STATUS_REJECTED = "rejected"

ACTIVE_BETA_APPLICATION_STATUSES = (
    BETA_APPLICATION_STATUS_PENDING,
    BETA_APPLICATION_STATUS_PROVISIONING,
    BETA_APPLICATION_STATUS_SUCCESS,
)
PROVISIONABLE_BETA_APPLICATION_STATUSES = (
    BETA_APPLICATION_STATUS_PENDING,
    BETA_APPLICATION_STATUS_FAILED,
)

RETRY_MODE_FROM_FAILED = "from_failed"
RETRY_MODE_FULL = "full"
SUPPORTED_RETRY_MODES = (
    RETRY_MODE_FROM_FAILED,
    RETRY_MODE_FULL,
)

STEP_STATUS_PENDING = "pending"
STEP_STATUS_RUNNING = "running"
STEP_STATUS_SUCCESS = "success"
STEP_STATUS_FAILED = "failed"
STEP_STATUS_RESERVED = "reserved"

PROVISION_TASK_STATUS_QUEUED = "queued"
PROVISION_TASK_STATUS_RUNNING = "running"
PROVISION_TASK_STATUS_SUCCESS = "success"
PROVISION_TASK_STATUS_FAILED = "failed"

STEP_SSO_CREATE_USER = "sso_create_user"
STEP_SSO_BIND_ROLE_PERMISSION = "sso_bind_role_permission"
STEP_FILEBAY_CREATE_USER = "filebay_create_user"
STEP_FILEBAY_CREATE_REPO = "filebay_create_repo"
STEP_FILEBAY_INIT_MASKED_DIR = "filebay_init_masked_dir"
STEP_NEXUS_RESOURCE_INIT = "nexus_resource_init"

PROVISION_STEP_ORDER = (
    STEP_SSO_CREATE_USER,
    STEP_SSO_BIND_ROLE_PERMISSION,
    STEP_FILEBAY_CREATE_USER,
    STEP_FILEBAY_CREATE_REPO,
    STEP_FILEBAY_INIT_MASKED_DIR,
    STEP_NEXUS_RESOURCE_INIT,
)

APPLICATION_STATUS_LABELS = {
    BETA_APPLICATION_STATUS_PENDING: "待审核",
    BETA_APPLICATION_STATUS_PROVISIONING: "开通中",
    BETA_APPLICATION_STATUS_SUCCESS: "开通成功",
    BETA_APPLICATION_STATUS_FAILED: "开通失败",
    BETA_APPLICATION_STATUS_REJECTED: "已拒绝",
}

STEP_STATUS_LABELS = {
    STEP_STATUS_PENDING: "未执行",
    STEP_STATUS_RUNNING: "执行中",
    STEP_STATUS_SUCCESS: "成功",
    STEP_STATUS_FAILED: "失败",
    STEP_STATUS_RESERVED: "预留",
}

STEP_LABELS = {
    STEP_SSO_CREATE_USER: "SSO 创建用户",
    STEP_SSO_BIND_ROLE_PERMISSION: "SSO 绑定默认角色",
    STEP_FILEBAY_CREATE_USER: "FileBay 创建用户",
    STEP_FILEBAY_CREATE_REPO: "FileBay 创建私有仓库",
    STEP_FILEBAY_INIT_MASKED_DIR: "FileBay 初始化脱敏目录",
    STEP_NEXUS_RESOURCE_INIT: "Nexus 资源初始化",
}

SENSITIVE_FIELDS = {"password", "client_secret", "authorization"}


@dataclass
class StepExecutionResult:
    request_payload: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None
    message: str | None = None


class BetaApplicationProvisionError(Exception):
    def __init__(
        self,
        *,
        step_key: str,
        message: str,
        request_payload: dict[str, Any] | None = None,
        response_payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.step_key = step_key
        self.message = message
        self.request_payload = request_payload
        self.response_payload = response_payload


class BetaApplicationProvisioningService:
    """Provision approved beta applicants into SSO and FileBay."""

    def __init__(self) -> None:
        self.http_timeout = max(1, int(dify_config.BETA_PROVISION_HTTP_TIMEOUT))
        self.max_manual_retry_count = max(0, int(dify_config.BETA_PROVISION_MAX_MANUAL_RETRY))
        self.enable_nexus_resource_init = dify_config.BETA_ENABLE_NEXUS_RESOURCE_INIT
        self.ssl_verify = dify_config.BETA_PROVISION_SSL_VERIFY
        if not self.ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.sso_base_url = self._normalize_sso_base_url(dify_config.SSO_API_URL)
        self.sso_owner = dify_config.SSO_PROVISION_OWNER
        self.sso_client_id = dify_config.SSO_PROVISION_CLIENT_ID or dify_config.DESKTOP_SSO_CLIENT_ID
        self.sso_client_secret = dify_config.SSO_PROVISION_CLIENT_SECRET or dify_config.DESKTOP_SSO_CLIENT_SECRET
        self.sso_default_role = dify_config.SSO_PROVISION_DEFAULT_ROLE
        self.sso_signup_application = dify_config.SSO_PROVISION_SIGNUP_APPLICATION

        self.filebay_base_url = (dify_config.FILEBAY_BASE_URL or dify_config.GITEA_URL).rstrip("/")
        self.filebay_admin_username = dify_config.FILEBAY_ADMIN_USERNAME
        self.filebay_admin_password = dify_config.FILEBAY_ADMIN_PASSWORD
        self.filebay_default_repo = dify_config.FILEBAY_DEFAULT_REPO
        self.filebay_default_branch = dify_config.FILEBAY_DEFAULT_BRANCH
        self.filebay_default_masked_dir = dify_config.FILEBAY_DEFAULT_MASKED_DIR.strip("/") or "masked"

    def provision(self, application: BetaApplication, *, retry_mode: str = RETRY_MODE_FULL) -> dict[str, Any]:
        if application.status not in PROVISIONABLE_BETA_APPLICATION_STATUSES:
            raise ValueError("Only pending or failed beta applications can be provisioned.")
        if retry_mode not in SUPPORTED_RETRY_MODES:
            raise ValueError(f"Unsupported retry mode: {retry_mode}.")

        original_status = application.status
        self._validate_required_config()
        self._ensure_step_rows(application.id)
        self._ensure_external_identifiers(application)

        application.status = BETA_APPLICATION_STATUS_PROVISIONING
        application.provision_attempt_count = (application.provision_attempt_count or 0) + 1
        application.provision_started_at = naive_utc_now()
        application.provision_finished_at = None
        application.last_error_step = None
        application.last_error_message = None
        db.session.add(application)
        db.session.commit()

        self._prepare_step6(application.id)
        step_keys = self._resolve_step_keys(application, original_status=original_status, retry_mode=retry_mode)

        try:
            for step_key in step_keys:
                self._run_step(application, step_key, self._get_step_executor(step_key))
        except BetaApplicationProvisionError as exc:
            logger.warning(
                "Beta application %s provisioning failed at %s: %s",
                application.id,
                exc.step_key,
                exc.message,
            )
            application.status = BETA_APPLICATION_STATUS_FAILED
            application.last_error_step = exc.step_key
            application.last_error_message = self._truncate(exc.message, 1000)
            application.provision_finished_at = naive_utc_now()
            db.session.add(application)
            db.session.commit()
            BetaApplicationNotificationService.send_provision_failed_email(
                application_id=application.id,
                to=application.email,
                name=application.name,
                language=application.language,
                error_message=application.last_error_message or exc.message,
            )
            raise
        except Exception as exc:  # pragma: no cover
            logger.exception("Unexpected beta application provisioning failure: %s", application.id)
            application.status = BETA_APPLICATION_STATUS_FAILED
            application.last_error_step = application.last_error_step or "unknown"
            application.last_error_message = self._truncate(str(exc), 1000)
            application.provision_finished_at = naive_utc_now()
            db.session.add(application)
            db.session.commit()
            BetaApplicationNotificationService.send_provision_failed_email(
                application_id=application.id,
                to=application.email,
                name=application.name,
                language=application.language,
                error_message=application.last_error_message or str(exc),
            )
            raise

        application.status = BETA_APPLICATION_STATUS_SUCCESS
        application.last_error_step = None
        application.last_error_message = None
        application.provision_finished_at = naive_utc_now()
        db.session.add(application)
        db.session.commit()
        BetaApplicationNotificationService.send_provision_success_email(
            application_id=application.id,
            to=application.email,
            name=application.name,
            language=application.language,
            sso_username=application.sso_username,
            sso_initial_password=None,
            filebay_repo=application.filebay_repo,
        )
        return self.serialize_application(application, include_steps=True)

    def approve(self, application: BetaApplication, *, reviewer_id: str | None = None) -> dict[str, Any]:
        if application.status != BETA_APPLICATION_STATUS_PENDING:
            raise ValueError("Only pending beta applications can be approved.")

        application.reviewer_id = reviewer_id
        application.reviewed_at = naive_utc_now()
        application.rejected_at = None
        application.rejection_reason = None
        db.session.add(application)
        db.session.commit()
        return self.provision(application, retry_mode=RETRY_MODE_FULL)

    def retry(self, application: BetaApplication, *, mode: str = RETRY_MODE_FROM_FAILED) -> dict[str, Any]:
        if application.status != BETA_APPLICATION_STATUS_FAILED:
            raise ValueError("Only failed beta applications can be retried.")
        if mode not in SUPPORTED_RETRY_MODES:
            raise ValueError(f"Unsupported retry mode: {mode}.")
        manual_retry_count = max((application.provision_attempt_count or 0) - 1, 0)
        if self.max_manual_retry_count > 0 and manual_retry_count >= self.max_manual_retry_count:
            raise ValueError(f"Manual retry limit reached ({self.max_manual_retry_count}).")
        return self.provision(application, retry_mode=mode)

    def reject(
        self,
        application: BetaApplication,
        reason: str,
        *,
        reviewer_id: str | None = None,
    ) -> dict[str, Any]:
        if application.status != BETA_APPLICATION_STATUS_PENDING:
            raise ValueError("Only pending beta applications can be rejected.")
        normalized_reason = (reason or "").strip()
        if not normalized_reason:
            raise ValueError("Reject reason is required.")
        if len(normalized_reason) < 5:
            raise ValueError("Reject reason must be at least 5 characters.")

        application.status = BETA_APPLICATION_STATUS_REJECTED
        application.reviewer_id = reviewer_id
        application.reviewed_at = naive_utc_now()
        application.rejected_at = naive_utc_now()
        application.rejection_reason = self._truncate(normalized_reason, 1000)
        application.last_error_step = None
        application.last_error_message = None
        db.session.add(application)
        db.session.commit()

        BetaApplicationNotificationService.send_rejected_email(
            application_id=application.id,
            to=application.email,
            name=application.name,
            language=application.language,
            reason=application.rejection_reason,
        )
        return self.serialize_application(application, include_steps=True)

    def list_steps(self, application_id: str) -> list[dict[str, Any]]:
        return [self.serialize_step(step) for step in self._get_ordered_steps(application_id)]

    def list_notifications(self, application_id: str) -> list[dict[str, Any]]:
        notifications = (
            db.session.query(BetaApplicationNotification)
            .filter(BetaApplicationNotification.application_id == application_id)
            .order_by(BetaApplicationNotification.created_at.desc())
            .all()
        )
        return [self.serialize_notification(item) for item in notifications]

    def list_provision_tasks(self, application_id: str) -> list[dict[str, Any]]:
        tasks = (
            db.session.query(BetaApplicationProvisionTask)
            .filter(BetaApplicationProvisionTask.application_id == application_id)
            .order_by(BetaApplicationProvisionTask.created_at.desc())
            .all()
        )
        return [self.serialize_provision_task(item) for item in tasks]

    def serialize_application(self, application: BetaApplication, *, include_steps: bool = False) -> dict[str, Any]:
        payload = {
            "id": application.id,
            "email": application.email,
            "name": application.name,
            "language": application.language,
            "company": application.company,
            "use_case": application.use_case,
            "status": application.status,
            "status_label": APPLICATION_STATUS_LABELS.get(application.status, application.status),
            "reviewer_id": application.reviewer_id,
            "reviewed_at": self._format_datetime(application.reviewed_at),
            "provision_attempt_count": application.provision_attempt_count,
            "provision_started_at": self._format_datetime(application.provision_started_at),
            "provision_finished_at": self._format_datetime(application.provision_finished_at),
            "rejected_at": self._format_datetime(application.rejected_at),
            "rejection_reason": application.rejection_reason,
            "last_error_step": application.last_error_step,
            "last_error_step_label": STEP_LABELS.get(application.last_error_step or "", application.last_error_step),
            "last_error_message": application.last_error_message,
            "sso_subject_id": application.sso_subject_id,
            "sso_username": application.sso_username,
            "filebay_username": application.filebay_username,
            "filebay_repo": application.filebay_repo,
            "created_at": self._format_datetime(application.created_at),
            "updated_at": self._format_datetime(application.updated_at),
        }
        if include_steps:
            payload["steps"] = self.list_steps(application.id)
        return payload

    def serialize_step(self, step: BetaApplicationStep) -> dict[str, Any]:
        return {
            "id": step.id,
            "application_id": step.application_id,
            "step_key": step.step_key,
            "step_label": STEP_LABELS.get(step.step_key, step.step_key),
            "status": step.status,
            "status_label": STEP_STATUS_LABELS.get(step.status, step.status),
            "message": step.message,
            "error_message": step.error_message,
            "attempt_count": step.attempt_count,
            "started_at": self._format_datetime(step.started_at),
            "finished_at": self._format_datetime(step.finished_at),
            "request_payload": self._deserialize_payload(step.request_payload),
            "response_payload": self._deserialize_payload(step.response_payload),
            "created_at": self._format_datetime(step.created_at),
            "updated_at": self._format_datetime(step.updated_at),
        }

    def serialize_notification(self, notification: BetaApplicationNotification) -> dict[str, Any]:
        return {
            "id": notification.id,
            "application_id": notification.application_id,
            "channel": notification.channel,
            "event": notification.event,
            "receiver": notification.receiver,
            "status": notification.status,
            "provider_message_id": notification.provider_message_id,
            "error_message": notification.error_message,
            "created_at": self._format_datetime(notification.created_at),
            "updated_at": self._format_datetime(notification.updated_at),
        }

    def serialize_provision_task(self, task: BetaApplicationProvisionTask) -> dict[str, Any]:
        return {
            "id": task.id,
            "application_id": task.application_id,
            "action": task.action,
            "mode": task.mode,
            "status": task.status,
            "celery_task_id": task.celery_task_id,
            "requested_by": task.requested_by,
            "requested_tenant_id": task.requested_tenant_id,
            "requested_ip": task.requested_ip,
            "error_message": task.error_message,
            "started_at": self._format_datetime(task.started_at),
            "finished_at": self._format_datetime(task.finished_at),
            "created_at": self._format_datetime(task.created_at),
            "updated_at": self._format_datetime(task.updated_at),
        }

    def _resolve_step_keys(
        self, application: BetaApplication, *, original_status: str, retry_mode: str
    ) -> tuple[str, ...]:
        executable_steps = tuple(
            step
            for step in PROVISION_STEP_ORDER
            if step != STEP_NEXUS_RESOURCE_INIT or self.enable_nexus_resource_init
        )
        if original_status != BETA_APPLICATION_STATUS_FAILED:
            return executable_steps
        if retry_mode == RETRY_MODE_FULL:
            return executable_steps

        failed_step = self._resolve_failed_step_key(application)
        if not failed_step:
            return executable_steps
        if failed_step not in executable_steps:
            return executable_steps
        failed_index = executable_steps.index(failed_step)
        return executable_steps[failed_index:]

    def _resolve_failed_step_key(self, application: BetaApplication) -> str | None:
        if (
            application.last_error_step in PROVISION_STEP_ORDER
            and application.last_error_step != STEP_NEXUS_RESOURCE_INIT
        ):
            return application.last_error_step

        ordered_steps = self._get_ordered_steps(application.id)
        for step in ordered_steps:
            if step.step_key == STEP_NEXUS_RESOURCE_INIT:
                continue
            if step.status == STEP_STATUS_FAILED:
                return step.step_key
        return None

    def _get_step_executor(self, step_key: str):
        executors = {
            STEP_SSO_CREATE_USER: self._sso_create_user,
            STEP_SSO_BIND_ROLE_PERMISSION: self._sso_bind_default_role,
            STEP_FILEBAY_CREATE_USER: self._filebay_create_user,
            STEP_FILEBAY_CREATE_REPO: self._filebay_create_repo,
            STEP_FILEBAY_INIT_MASKED_DIR: self._filebay_init_masked_dir,
            STEP_NEXUS_RESOURCE_INIT: self._nexus_resource_init,
        }
        if step_key not in executors:
            raise ValueError(f"Unknown beta provisioning step: {step_key}.")
        return executors[step_key]

    def _run_step(self, application: BetaApplication, step_key: str, executor: Any) -> None:
        step = self._get_step(application.id, step_key)
        step.status = STEP_STATUS_RUNNING
        step.message = None
        step.error_message = None
        step.started_at = naive_utc_now()
        step.finished_at = None
        step.attempt_count = (step.attempt_count or 0) + 1
        db.session.add(step)
        db.session.commit()

        try:
            result = executor(application)
        except BetaApplicationProvisionError as exc:
            if exc.step_key != step_key:
                exc = BetaApplicationProvisionError(
                    step_key=step_key,
                    message=exc.message,
                    request_payload=exc.request_payload,
                    response_payload=exc.response_payload,
                )
            step.status = STEP_STATUS_FAILED
            step.message = self._truncate(exc.message, 500)
            step.error_message = self._truncate(exc.message, 5000)
            step.request_payload = self._serialize_payload(exc.request_payload)
            step.response_payload = self._serialize_payload(exc.response_payload)
            step.finished_at = naive_utc_now()
            db.session.add(step)
            db.session.commit()
            raise
        except Exception as exc:  # pragma: no cover
            step.status = STEP_STATUS_FAILED
            step.message = self._truncate(str(exc), 500)
            step.error_message = self._truncate(str(exc), 5000)
            step.finished_at = naive_utc_now()
            db.session.add(step)
            db.session.commit()
            raise BetaApplicationProvisionError(step_key=step_key, message=str(exc)) from exc

        step.status = STEP_STATUS_SUCCESS
        step.message = self._truncate(result.message or "ok", 500)
        step.error_message = None
        step.request_payload = self._serialize_payload(result.request_payload)
        step.response_payload = self._serialize_payload(result.response_payload)
        step.finished_at = naive_utc_now()
        db.session.add(step)
        db.session.commit()

    def _sso_create_user(self, application: BetaApplication) -> StepExecutionResult:
        username = application.sso_username or self._generate_username(application.email)
        subject_ref = f"{self.sso_owner}/{username}"
        application.sso_username = username
        application.sso_subject_id = subject_ref
        db.session.add(application)
        db.session.commit()

        existing_user = self._sso_get_user(username)
        if existing_user:
            return StepExecutionResult(
                request_payload={"username": username, "email": application.email},
                response_payload={"status": "already_exists", "user": self._mask_payload(existing_user)},
                message="SSO user already exists",
            )

        password = self._generate_password()
        request_payload = {
            "owner": self.sso_owner,
            "name": username,
            "displayName": application.name or username,
            "email": application.email,
            "password": password,
            "type": "normal-user",
            "signupApplication": self.sso_signup_application,
        }
        response = self._request(
            method="POST",
            base_url=self.sso_base_url,
            path="/api/add-user",
            auth=(self.sso_client_id, self.sso_client_secret),
            json_payload=request_payload,
        )
        if response.status_code not in (200, 201) and not self._looks_like_already_exists(response):
            raise BetaApplicationProvisionError(
                step_key=STEP_SSO_CREATE_USER,
                message=self._build_http_error("SSO create user failed", response),
                request_payload=self._mask_payload(request_payload),
                response_payload=self._build_response_snapshot(response),
            )

        created_user = self._sso_get_user(username)
        if not created_user:
            raise BetaApplicationProvisionError(
                step_key=STEP_SSO_CREATE_USER,
                message="SSO user creation request succeeded, but user lookup still returned empty.",
                request_payload=self._mask_payload(request_payload),
                response_payload=self._build_response_snapshot(response),
            )

        return StepExecutionResult(
            request_payload=self._mask_payload(request_payload),
            response_payload={"status_code": response.status_code, "user": self._mask_payload(created_user)},
            message="SSO user created successfully",
        )

    def _sso_bind_default_role(self, application: BetaApplication) -> StepExecutionResult:
        username = application.sso_username or self._generate_username(application.email)
        subject_ref = application.sso_subject_id or f"{self.sso_owner}/{username}"
        role_id = f"{self.sso_owner}/{self.sso_default_role}"

        role_response = self._request(
            method="GET",
            base_url=self.sso_base_url,
            path="/api/get-role",
            auth=(self.sso_client_id, self.sso_client_secret),
            params={"id": role_id},
        )
        if role_response.status_code != 200:
            raise BetaApplicationProvisionError(
                step_key=STEP_SSO_BIND_ROLE_PERMISSION,
                message=self._build_http_error("SSO get role failed", role_response),
                request_payload={"role_id": role_id, "subject_ref": subject_ref},
                response_payload=self._build_response_snapshot(role_response),
            )

        role_payload = self._extract_data(role_response)
        if not isinstance(role_payload, dict):
            raise BetaApplicationProvisionError(
                step_key=STEP_SSO_BIND_ROLE_PERMISSION,
                message="SSO role query returned invalid payload.",
                request_payload={"role_id": role_id, "subject_ref": subject_ref},
                response_payload=self._build_response_snapshot(role_response),
            )

        current_users = role_payload.get("users") or []
        if subject_ref in current_users:
            return StepExecutionResult(
                request_payload={"role_id": role_id, "subject_ref": subject_ref},
                response_payload={"status": "already_bound"},
                message="SSO default role already assigned",
            )

        role_payload["users"] = list(dict.fromkeys([*current_users, subject_ref]))
        update_response = self._request(
            method="POST",
            base_url=self.sso_base_url,
            path="/api/update-role",
            auth=(self.sso_client_id, self.sso_client_secret),
            params={"id": role_id},
            json_payload=role_payload,
        )
        if update_response.status_code not in (200, 201):
            raise BetaApplicationProvisionError(
                step_key=STEP_SSO_BIND_ROLE_PERMISSION,
                message=self._build_http_error("SSO update role failed", update_response),
                request_payload={"role_id": role_id, "subject_ref": subject_ref},
                response_payload=self._build_response_snapshot(update_response),
            )

        return StepExecutionResult(
            request_payload={"role_id": role_id, "subject_ref": subject_ref},
            response_payload=self._build_response_snapshot(update_response),
            message="SSO default role assigned successfully",
        )

    def _filebay_create_user(self, application: BetaApplication) -> StepExecutionResult:
        username = application.filebay_username or self._generate_username(application.email)
        application.filebay_username = username
        db.session.add(application)
        db.session.commit()

        existing_user = self._filebay_get_user(username)
        if existing_user:
            return StepExecutionResult(
                request_payload={"username": username, "email": application.email},
                response_payload={"status": "already_exists", "user": self._mask_payload(existing_user)},
                message="FileBay user already exists",
            )

        password = self._generate_password()
        request_payload = {
            "username": username,
            "email": application.email,
            "password": password,
            "must_change_password": True,
            "visibility": "private",
            "send_notify": False,
        }
        response = self._request(
            method="POST",
            base_url=self.filebay_base_url,
            path="/api/v1/admin/users",
            auth=(self.filebay_admin_username, self.filebay_admin_password),
            json_payload=request_payload,
        )
        if response.status_code not in (200, 201) and not self._looks_like_already_exists(response):
            raise BetaApplicationProvisionError(
                step_key=STEP_FILEBAY_CREATE_USER,
                message=self._build_http_error("FileBay create user failed", response),
                request_payload=self._mask_payload(request_payload),
                response_payload=self._build_response_snapshot(response),
            )

        created_user = self._filebay_get_user(username)
        if not created_user:
            raise BetaApplicationProvisionError(
                step_key=STEP_FILEBAY_CREATE_USER,
                message="FileBay user creation request succeeded, but user lookup still returned empty.",
                request_payload=self._mask_payload(request_payload),
                response_payload=self._build_response_snapshot(response),
            )

        return StepExecutionResult(
            request_payload=self._mask_payload(request_payload),
            response_payload={"status_code": response.status_code, "user": self._mask_payload(created_user)},
            message="FileBay user created successfully",
        )

    def _filebay_create_repo(self, application: BetaApplication) -> StepExecutionResult:
        username = application.filebay_username or self._generate_username(application.email)
        repo_name = application.filebay_repo or self.filebay_default_repo
        application.filebay_repo = repo_name
        db.session.add(application)
        db.session.commit()

        existing_repo = self._filebay_get_repo(username, repo_name)
        if existing_repo:
            return StepExecutionResult(
                request_payload={"owner": username, "repo": repo_name},
                response_payload={"status": "already_exists", "repo": self._mask_payload(existing_repo)},
                message="FileBay repository already exists",
            )

        request_payload = {
            "name": repo_name,
            "private": True,
            "auto_init": True,
            "default_branch": self.filebay_default_branch,
        }
        response = self._request(
            method="POST",
            base_url=self.filebay_base_url,
            path=f"/api/v1/admin/users/{username}/repos",
            auth=(self.filebay_admin_username, self.filebay_admin_password),
            json_payload=request_payload,
        )
        if response.status_code not in (200, 201) and not self._looks_like_already_exists(response):
            raise BetaApplicationProvisionError(
                step_key=STEP_FILEBAY_CREATE_REPO,
                message=self._build_http_error("FileBay create repo failed", response),
                request_payload={"owner": username, **request_payload},
                response_payload=self._build_response_snapshot(response),
            )

        created_repo = self._filebay_get_repo(username, repo_name)
        if not created_repo:
            raise BetaApplicationProvisionError(
                step_key=STEP_FILEBAY_CREATE_REPO,
                message="FileBay repository creation request succeeded, but repository lookup still returned empty.",
                request_payload={"owner": username, **request_payload},
                response_payload=self._build_response_snapshot(response),
            )

        return StepExecutionResult(
            request_payload={"owner": username, **request_payload},
            response_payload={"status_code": response.status_code, "repo": self._mask_payload(created_repo)},
            message="FileBay repository created successfully",
        )

    def _filebay_init_masked_dir(self, application: BetaApplication) -> StepExecutionResult:
        username = application.filebay_username or self._generate_username(application.email)
        repo_name = application.filebay_repo or self.filebay_default_repo
        placeholder_path = f"{self.filebay_default_masked_dir}/.keep"

        existing_file = self._filebay_get_content(username, repo_name, placeholder_path)
        if existing_file:
            return StepExecutionResult(
                request_payload={"owner": username, "repo": repo_name, "path": placeholder_path},
                response_payload={"status": "already_exists"},
                message="FileBay masked directory already initialized",
            )

        request_payload = {
            "message": f"init {self.filebay_default_masked_dir} directory",
            "content": base64.b64encode(b"# keep\n").decode("utf-8"),
            "branch": self.filebay_default_branch,
        }
        response = self._request(
            method="POST",
            base_url=self.filebay_base_url,
            path=f"/api/v1/repos/{username}/{repo_name}/contents/{placeholder_path}",
            auth=(self.filebay_admin_username, self.filebay_admin_password),
            json_payload=request_payload,
        )
        if response.status_code not in (200, 201) and not self._looks_like_already_exists(response):
            raise BetaApplicationProvisionError(
                step_key=STEP_FILEBAY_INIT_MASKED_DIR,
                message=self._build_http_error("FileBay init masked directory failed", response),
                request_payload={"owner": username, "repo": repo_name, "path": placeholder_path, **request_payload},
                response_payload=self._build_response_snapshot(response),
            )

        return StepExecutionResult(
            request_payload={"owner": username, "repo": repo_name, "path": placeholder_path, **request_payload},
            response_payload=self._build_response_snapshot(response),
            message="FileBay masked directory initialized successfully",
        )

    def _ensure_step_rows(self, application_id: str) -> None:
        existing_steps = {
            step.step_key: step
            for step in db.session.query(BetaApplicationStep)
            .filter(BetaApplicationStep.application_id == application_id)
            .all()
        }
        created = False
        for step_key in PROVISION_STEP_ORDER:
            if step_key in existing_steps:
                continue
            created = True
            db.session.add(
                BetaApplicationStep(
                    id=str(uuid4()),
                    application_id=application_id,
                    step_key=step_key,
                    status=STEP_STATUS_RESERVED if step_key == STEP_NEXUS_RESOURCE_INIT else STEP_STATUS_PENDING,
                )
            )
        if created:
            db.session.commit()

    def _prepare_step6(self, application_id: str) -> None:
        step = self._get_step(application_id, STEP_NEXUS_RESOURCE_INIT)
        if self.enable_nexus_resource_init:
            step.status = STEP_STATUS_PENDING
            step.message = None
            step.error_message = None
            step.request_payload = None
            step.response_payload = None
            step.started_at = None
            step.finished_at = None
        else:
            step.status = STEP_STATUS_RESERVED
            step.message = "Reserved for future Nexus workflow integration."
            step.error_message = None
            step.request_payload = None
            step.response_payload = None
            step.started_at = None
            step.finished_at = None
        db.session.add(step)
        db.session.commit()

    def _nexus_resource_init(self, application: BetaApplication) -> StepExecutionResult:
        request_payload = {
            "application_id": application.id,
            "mode": "default",
        }
        response_payload = {
            "status": "ok",
            "message": "nexus resource init completed",
        }
        return StepExecutionResult(
            request_payload=request_payload,
            response_payload=response_payload,
            message="Nexus resource initialized",
        )

    def _ensure_external_identifiers(self, application: BetaApplication) -> None:
        username = (
            application.sso_username
            or application.filebay_username
            or self._generate_username(application.email)
        )
        application.sso_username = username
        application.filebay_username = username
        application.sso_subject_id = application.sso_subject_id or f"{self.sso_owner}/{username}"
        application.filebay_repo = application.filebay_repo or self.filebay_default_repo
        db.session.add(application)
        db.session.commit()

    def _get_step(self, application_id: str, step_key: str) -> BetaApplicationStep:
        step = (
            db.session.query(BetaApplicationStep)
            .filter(
                BetaApplicationStep.application_id == application_id,
                BetaApplicationStep.step_key == step_key,
            )
            .first()
        )
        if not step:
            raise ValueError(f"Provision step {step_key} not initialized for application {application_id}.")
        return step

    def _get_ordered_steps(self, application_id: str) -> list[BetaApplicationStep]:
        steps = db.session.query(BetaApplicationStep).filter(BetaApplicationStep.application_id == application_id).all()
        step_order = {step_key: index for index, step_key in enumerate(PROVISION_STEP_ORDER)}
        return sorted(steps, key=lambda item: step_order.get(item.step_key, len(PROVISION_STEP_ORDER)))

    def _validate_required_config(self) -> None:
        missing_fields: list[str] = []
        if not self.sso_base_url:
            missing_fields.append("SSO_API_URL")
        if not self.sso_client_id:
            missing_fields.append("SSO_PROVISION_CLIENT_ID or DESKTOP_SSO_CLIENT_ID")
        if not self.sso_client_secret:
            missing_fields.append("SSO_PROVISION_CLIENT_SECRET or DESKTOP_SSO_CLIENT_SECRET")
        if not self.filebay_base_url:
            missing_fields.append("FILEBAY_BASE_URL or GITEA_URL")
        if not self.filebay_admin_username:
            missing_fields.append("FILEBAY_ADMIN_USERNAME")
        if not self.filebay_admin_password:
            missing_fields.append("FILEBAY_ADMIN_PASSWORD")

        if missing_fields:
            raise ValueError(f"Missing beta provisioning config: {', '.join(missing_fields)}")

    def _sso_get_user(self, username: str) -> dict[str, Any] | None:
        response = self._request(
            method="GET",
            base_url=self.sso_base_url,
            path="/api/get-user",
            auth=(self.sso_client_id, self.sso_client_secret),
            params={"id": f"{self.sso_owner}/{username}"},
        )
        if response.status_code != 200:
            return None
        payload = self._extract_data(response)
        return payload if isinstance(payload, dict) else None

    def _filebay_get_user(self, username: str) -> dict[str, Any] | None:
        response = self._request(
            method="GET",
            base_url=self.filebay_base_url,
            path=f"/api/v1/users/{username}",
            auth=(self.filebay_admin_username, self.filebay_admin_password),
        )
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            return None
        return self._extract_json_dict(response)

    def _filebay_get_repo(self, owner: str, repo_name: str) -> dict[str, Any] | None:
        response = self._request(
            method="GET",
            base_url=self.filebay_base_url,
            path=f"/api/v1/repos/{owner}/{repo_name}",
            auth=(self.filebay_admin_username, self.filebay_admin_password),
        )
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            return None
        return self._extract_json_dict(response)

    def _filebay_get_content(self, owner: str, repo_name: str, path: str) -> dict[str, Any] | None:
        response = self._request(
            method="GET",
            base_url=self.filebay_base_url,
            path=f"/api/v1/repos/{owner}/{repo_name}/contents/{path}",
            auth=(self.filebay_admin_username, self.filebay_admin_password),
        )
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            return None
        return self._extract_json_dict(response)

    def _request(
        self,
        *,
        method: str,
        base_url: str,
        path: str,
        auth: tuple[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> requests.Response:
        url = f"{base_url.rstrip('/')}{path}"
        try:
            return requests.request(
                method=method,
                url=url,
                auth=auth,
                params=params,
                json=json_payload,
                timeout=self.http_timeout,
                verify=self.ssl_verify,
            )
        except requests.RequestException as exc:
            raise BetaApplicationProvisionError(
                step_key="network",
                message=f"Request to {url} failed: {exc}",
                request_payload={"params": params, "body": self._mask_payload(json_payload)},
            ) from exc

    def _extract_data(self, response: requests.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            return None
        if isinstance(payload, dict) and "data" in payload:
            return payload.get("data")
        return payload

    def _extract_json_dict(self, response: requests.Response) -> dict[str, Any] | None:
        try:
            payload = response.json()
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None

    def _build_response_snapshot(self, response: requests.Response) -> dict[str, Any]:
        snapshot: dict[str, Any] = {"status_code": response.status_code}
        payload = self._extract_json_dict(response)
        if payload is not None:
            snapshot["body"] = self._mask_payload(payload)
        else:
            snapshot["body"] = self._truncate(response.text, 1000)
        return snapshot

    def _build_http_error(self, prefix: str, response: requests.Response) -> str:
        body = self._extract_json_dict(response)
        if body:
            message = body.get("msg") or body.get("message") or body.get("error_description") or body.get("error")
            if message:
                return f"{prefix}: {message}"
        return f"{prefix}: HTTP {response.status_code}"

    def _looks_like_already_exists(self, response: requests.Response) -> bool:
        if response.status_code in (409, 422):
            return True

        body = self._extract_json_dict(response)
        candidates = [
            body.get("msg") if isinstance(body, dict) else None,
            body.get("message") if isinstance(body, dict) else None,
            body.get("error_description") if isinstance(body, dict) else None,
            response.text,
        ]
        normalized = " ".join(filter(None, candidates)).lower()
        return any(keyword in normalized for keyword in ("already exists", "has been taken", "duplicate", "already"))

    def _generate_username(self, email: str) -> str:
        email = (email or "").strip().lower()
        base = re.sub(r"[^a-z0-9]+", "_", email).strip("_") or "beta_user"
        suffix = hashlib.sha1(email.encode("utf-8")).hexdigest()[:6]
        trimmed_base = base[:32].rstrip("_") or "beta_user"
        return f"{trimmed_base}_{suffix}"[:39]

    def _generate_password(self, length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits
        random_part = "".join(secrets.choice(alphabet) for _ in range(max(8, length - 4)))
        return f"Aa1!{random_part}"[:length]

    def _serialize_payload(self, payload: dict[str, Any] | None) -> str | None:
        if payload is None:
            return None
        return json.dumps(self._mask_payload(payload), ensure_ascii=False)

    def _deserialize_payload(self, payload: str | None) -> Any:
        if not payload:
            return None
        try:
            return json.loads(payload)
        except ValueError:
            return payload

    def _mask_payload(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            masked: dict[str, Any] = {}
            for key, value in payload.items():
                if key.lower() in SENSITIVE_FIELDS:
                    masked[key] = "***"
                else:
                    masked[key] = self._mask_payload(value)
            return masked
        if isinstance(payload, list):
            return [self._mask_payload(item) for item in payload]
        return payload

    def _format_datetime(self, value: Any) -> str | None:
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def _normalize_sso_base_url(self, value: str) -> str:
        normalized = (value or "").rstrip("/")
        if normalized.endswith("/api"):
            return normalized[:-4]
        return normalized

    def _truncate(self, value: str | None, max_length: int) -> str | None:
        if value is None:
            return None
        if len(value) <= max_length:
            return value
        return value[: max_length - 3] + "..."
