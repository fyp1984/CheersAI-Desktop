from typing import Literal

from flask_restx import Resource
from pydantic import BaseModel, Field, model_validator

from controllers.common.schema import register_schema_model
from controllers.console.wraps import setup_required
from controllers.inner_api import inner_api_ns
from controllers.inner_api.wraps import enterprise_inner_api_only
from services.beta_application_notification_service import BetaApplicationNotificationService


class BetaNotificationPayload(BaseModel):
    event: Literal["submitted", "approved", "rejected", "provision_failed"]
    to: str = Field(..., description="Recipient email address")
    name: str | None = Field(default=None, description="Display name")
    language: str | None = Field(default="zh-Hans", description="Language code")
    reason: str | None = Field(default=None, description="Rejection reason")
    sso_username: str | None = Field(default=None, description="Provisioned SSO username")
    sso_initial_password: str | None = Field(default=None, description="Provisioned SSO temporary password")
    filebay_repo: str | None = Field(default=None, description="Provisioned FileBay repository")
    error_message: str | None = Field(default=None, description="Provisioning error details")
    application_id: str | None = Field(default=None, description="Optional legacy beta application id")

    @model_validator(mode="after")
    def validate_event_fields(self):
        if self.event == "rejected" and not self.reason:
            raise ValueError("reason is required when event is rejected")
        if self.event == "approved" and not self.sso_username:
            raise ValueError("sso_username is required when event is approved")
        if self.event == "approved" and not self.filebay_repo:
            raise ValueError("filebay_repo is required when event is approved")
        if self.event == "provision_failed" and not self.error_message:
            raise ValueError("error_message is required when event is provision_failed")
        return self


register_schema_model(inner_api_ns, BetaNotificationPayload)


@inner_api_ns.route("/enterprise/beta-notifications")
class EnterpriseBetaNotification(Resource):
    method_decorators = [setup_required, enterprise_inner_api_only]

    @inner_api_ns.doc("send_beta_notification")
    @inner_api_ns.doc(description="Send beta application notification email")
    @inner_api_ns.expect(inner_api_ns.models[BetaNotificationPayload.__name__])
    @inner_api_ns.doc(
        responses={200: "Notification processed", 401: "Unauthorized - invalid API key", 404: "Service not available"}
    )
    def post(self):
        args = BetaNotificationPayload.model_validate(inner_api_ns.payload or {})

        delivered = self._dispatch(args)
        return {"message": "success", "delivered": delivered}, 200

    @staticmethod
    def _dispatch(args: BetaNotificationPayload) -> bool:
        if args.event == "submitted":
            return BetaApplicationNotificationService.send_submitted_email(
                application_id=args.application_id,
                to=args.to,
                name=args.name,
                language=args.language,
                sync=True,
            )
        if args.event == "approved":
            return BetaApplicationNotificationService.send_provision_success_email(
                application_id=args.application_id,
                to=args.to,
                name=args.name,
                language=args.language,
                sso_username=args.sso_username,
                sso_initial_password=args.sso_initial_password,
                filebay_repo=args.filebay_repo,
                sync=True,
            )
        if args.event == "rejected":
            return BetaApplicationNotificationService.send_rejected_email(
                application_id=args.application_id,
                to=args.to,
                name=args.name,
                language=args.language,
                reason=args.reason or "",
                sync=True,
            )
        return BetaApplicationNotificationService.send_provision_failed_email(
            application_id=args.application_id,
            to=args.to,
            name=args.name,
            language=args.language,
            error_message=args.error_message or "",
            sync=True,
        )
