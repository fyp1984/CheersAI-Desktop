from uuid import uuid4

from flask import request
from flask_restx import Resource
from pydantic import BaseModel, Field

from controllers.console import console_ns
from controllers.console.wraps import is_admin_or_owner_required, setup_required
from extensions.ext_database import db
from libs.login import current_account_with_tenant, login_required
from models.beta_application import BetaApplication
from models.beta_application_provision_task import BetaApplicationProvisionTask
from models.model import OperationLog
from services.beta_application_provisioning_service import (
    ACTIVE_BETA_APPLICATION_STATUSES,
    RETRY_MODE_FROM_FAILED,
    SUPPORTED_RETRY_MODES,
    BetaApplicationProvisionError,
    BetaApplicationProvisioningService,
)
from tasks.beta_application_provision_task import (
    ACTION_APPROVE,
    ACTION_RETRY,
    run_beta_application_provision_task,
)

DEFAULT_REF_TEMPLATE_SWAGGER_2_0 = "#/definitions/{model}"


class RejectBetaApplicationPayload(BaseModel):
    reason: str = Field(..., description="Reject reason")


class RetryBetaApplicationPayload(BaseModel):
    mode: str = Field(default=RETRY_MODE_FROM_FAILED, description="Retry mode: from_failed or full")


def reg(cls: type[BaseModel]):
    console_ns.schema_model(cls.__name__, cls.model_json_schema(ref_template=DEFAULT_REF_TEMPLATE_SWAGGER_2_0))


reg(RejectBetaApplicationPayload)
reg(RetryBetaApplicationPayload)


def _get_beta_application(application_id: str) -> BetaApplication | None:
    return db.session.query(BetaApplication).filter(BetaApplication.id == application_id).first()


def _record_operation_log(
    *,
    account_id: str,
    tenant_id: str,
    action: str,
    application_id: str,
    result: str,
    message: str | None = None,
    task_id: str | None = None,
    extra: dict | None = None,
):
    content = {
        "application_id": application_id,
        "result": result,
        "message": message,
        "task_id": task_id,
    }
    if extra:
        content.update(extra)

    try:
        db.session.add(
            OperationLog(
                tenant_id=tenant_id,
                account_id=account_id,
                action=action,
                content=content,
                created_ip=(request.remote_addr or "unknown")[:255],
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()


def _enqueue_provision_task(
    *,
    application_id: str,
    action: str,
    mode: str | None,
    requested_by: str,
    requested_tenant_id: str,
) -> BetaApplicationProvisionTask:
    provision_task = BetaApplicationProvisionTask(
        id=str(uuid4()),
        application_id=application_id,
        action=action,
        mode=mode,
        status="queued",
        requested_by=requested_by,
        requested_tenant_id=requested_tenant_id,
        requested_ip=(request.remote_addr or "")[:255],
    )
    db.session.add(provision_task)
    db.session.commit()

    try:
        async_result = run_beta_application_provision_task.delay(provision_task.id)
        provision_task.celery_task_id = async_result.id
        db.session.add(provision_task)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        provision_task = (
            db.session.query(BetaApplicationProvisionTask)
            .filter(BetaApplicationProvisionTask.id == provision_task.id)
            .first()
        )
        if provision_task:
            provision_task.status = "failed"
            provision_task.error_message = f"Failed to dispatch celery task: {exc}"[:5000]
            db.session.add(provision_task)
            db.session.commit()
        raise
    return provision_task


@console_ns.route("/beta-applications")
class BetaApplicationListApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    def get(self):
        status = request.args.get("status", "").strip()
        email = request.args.get("email", "").strip().lower()
        try:
            limit = min(max(int(request.args.get("limit", 20)), 1), 100)
        except ValueError:
            limit = 20

        query = db.session.query(BetaApplication)
        if status:
            query = query.filter(BetaApplication.status == status)
        if email:
            query = query.filter(BetaApplication.email.ilike(f"%{email}%"))

        items = query.order_by(BetaApplication.created_at.desc()).limit(limit).all()
        service = BetaApplicationProvisioningService()
        return {
            "items": [service.serialize_application(item) for item in items],
            "total": len(items),
            "active_duplicate_statuses": list(ACTIVE_BETA_APPLICATION_STATUSES),
        }


@console_ns.route("/beta-applications/<string:application_id>")
class BetaApplicationDetailApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    def get(self, application_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        service = BetaApplicationProvisioningService()
        return {
            "result": "success",
            "application": service.serialize_application(application, include_steps=True),
            "provision_tasks": service.list_provision_tasks(application_id),
            "notifications": service.list_notifications(application_id),
        }


@console_ns.route("/beta-applications/<string:application_id>/steps")
class BetaApplicationStepsApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    def get(self, application_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        service = BetaApplicationProvisioningService()
        return {"result": "success", "steps": service.list_steps(application_id)}


@console_ns.route("/beta-applications/<string:application_id>/notifications")
class BetaApplicationNotificationsApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    def get(self, application_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        service = BetaApplicationProvisioningService()
        return {"result": "success", "notifications": service.list_notifications(application_id)}


@console_ns.route("/beta-applications/<string:application_id>/provision-tasks")
class BetaApplicationProvisionTaskListApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    def get(self, application_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        service = BetaApplicationProvisioningService()
        return {"result": "success", "tasks": service.list_provision_tasks(application_id)}


@console_ns.route("/beta-applications/<string:application_id>/provision-tasks/<string:task_id>")
class BetaApplicationProvisionTaskDetailApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    def get(self, application_id: str, task_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        task = (
            db.session.query(BetaApplicationProvisionTask)
            .filter(
                BetaApplicationProvisionTask.id == task_id,
                BetaApplicationProvisionTask.application_id == application_id,
            )
            .first()
        )
        if not task:
            return {"result": "fail", "message": "Provision task not found."}, 404

        service = BetaApplicationProvisioningService()
        return {"result": "success", "task": service.serialize_provision_task(task)}


@console_ns.route("/beta-applications/<string:application_id>/provision")
class BetaApplicationProvisionApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    def post(self, application_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        current_user, current_tenant_id = current_account_with_tenant()
        service = BetaApplicationProvisioningService()
        try:
            result = service.provision(application)
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.provision",
                application_id=application_id,
                result="success",
                message="manual provision completed",
            )
        except ValueError as exc:
            db.session.rollback()
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.provision",
                application_id=application_id,
                result="fail",
                message=str(exc),
            )
            return {"result": "fail", "message": str(exc)}, 400
        except BetaApplicationProvisionError as exc:
            db.session.rollback()
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.provision",
                application_id=application_id,
                result="fail",
                message=exc.message,
            )
            application = _get_beta_application(application_id)
            return {
                "result": "fail",
                "message": exc.message,
                "application": service.serialize_application(application, include_steps=True) if application else None,
            }, 502
        except Exception as exc:
            db.session.rollback()
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.provision",
                application_id=application_id,
                result="fail",
                message=str(exc),
            )
            application = _get_beta_application(application_id)
            return {
                "result": "fail",
                "message": str(exc),
                "application": service.serialize_application(application, include_steps=True) if application else None,
            }, 500

        return {
            "result": "success",
            "message": "Beta application provisioned successfully.",
            "application": result,
        }


@console_ns.route("/beta-applications/<string:application_id>/approve")
class BetaApplicationApproveApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    def post(self, application_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        current_user, current_tenant_id = current_account_with_tenant()
        if application.status != "pending":
            return {"result": "fail", "message": "Only pending beta applications can be approved."}, 400

        service = BetaApplicationProvisioningService()
        try:
            provision_task = _enqueue_provision_task(
                application_id=application_id,
                action=ACTION_APPROVE,
                mode=None,
                requested_by=current_user.id,
                requested_tenant_id=current_tenant_id,
            )
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.approve.dispatch",
                application_id=application_id,
                result="success",
                task_id=provision_task.id,
                message="approve task dispatched",
                extra={"celery_task_id": provision_task.celery_task_id},
            )
        except Exception as exc:
            db.session.rollback()
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.approve.dispatch",
                application_id=application_id,
                result="fail",
                message=str(exc),
            )
            return {
                "result": "fail",
                "message": str(exc),
            }, 500

        return {
            "result": "success",
            "message": "Beta application approve task dispatched.",
            "task": service.serialize_provision_task(provision_task),
            "application": service.serialize_application(application),
        }


@console_ns.route("/beta-applications/<string:application_id>/retry")
class BetaApplicationRetryApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    @console_ns.expect(console_ns.models[RetryBetaApplicationPayload.__name__])
    def post(self, application_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        payload = RetryBetaApplicationPayload.model_validate(console_ns.payload or {})
        if application.status != "failed":
            return {"result": "fail", "message": "Only failed beta applications can be retried."}, 400

        current_user, current_tenant_id = current_account_with_tenant()
        service = BetaApplicationProvisioningService()
        if payload.mode not in SUPPORTED_RETRY_MODES:
            return {"result": "fail", "message": f"Unsupported retry mode: {payload.mode}."}, 400
        manual_retry_count = max((application.provision_attempt_count or 0) - 1, 0)
        if service.max_manual_retry_count > 0 and manual_retry_count >= service.max_manual_retry_count:
            return {"result": "fail", "message": f"Manual retry limit reached ({service.max_manual_retry_count})."}, 400
        try:
            provision_task = _enqueue_provision_task(
                application_id=application_id,
                action=ACTION_RETRY,
                mode=payload.mode,
                requested_by=current_user.id,
                requested_tenant_id=current_tenant_id,
            )
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.retry.dispatch",
                application_id=application_id,
                result="success",
                task_id=provision_task.id,
                message="retry task dispatched",
                extra={"mode": payload.mode, "celery_task_id": provision_task.celery_task_id},
            )
        except ValueError as exc:
            db.session.rollback()
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.retry.dispatch",
                application_id=application_id,
                result="fail",
                message=str(exc),
                extra={"mode": payload.mode},
            )
            return {"result": "fail", "message": str(exc)}, 400
        except Exception as exc:
            db.session.rollback()
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.retry.dispatch",
                application_id=application_id,
                result="fail",
                message=str(exc),
                extra={"mode": payload.mode},
            )
            return {
                "result": "fail",
                "message": str(exc),
            }, 500

        return {
            "result": "success",
            "message": "Beta application retry task dispatched.",
            "task": service.serialize_provision_task(provision_task),
            "application": service.serialize_application(application),
        }


@console_ns.route("/beta-applications/<string:application_id>/reject")
class BetaApplicationRejectApi(Resource):
    @setup_required
    @login_required
    @is_admin_or_owner_required
    @console_ns.expect(console_ns.models[RejectBetaApplicationPayload.__name__])
    def post(self, application_id: str):
        application = _get_beta_application(application_id)
        if not application:
            return {"result": "fail", "message": "Beta application not found."}, 404

        payload = RejectBetaApplicationPayload.model_validate(console_ns.payload or {})
        service = BetaApplicationProvisioningService()
        current_user, current_tenant_id = current_account_with_tenant()
        try:
            result = service.reject(application, payload.reason, reviewer_id=current_user.id)
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.reject",
                application_id=application_id,
                result="success",
                message="application rejected",
            )
        except ValueError as exc:
            db.session.rollback()
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.reject",
                application_id=application_id,
                result="fail",
                message=str(exc),
            )
            return {"result": "fail", "message": str(exc)}, 400
        except Exception as exc:
            db.session.rollback()
            _record_operation_log(
                account_id=current_user.id,
                tenant_id=current_tenant_id,
                action="beta_application.reject",
                application_id=application_id,
                result="fail",
                message=str(exc),
            )
            application = _get_beta_application(application_id)
            return {
                "result": "fail",
                "message": str(exc),
                "application": service.serialize_application(application, include_steps=True) if application else None,
            }, 500

        return {
            "result": "success",
            "message": "Beta application rejected successfully.",
            "application": result,
        }
