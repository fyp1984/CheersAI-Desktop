from uuid import uuid4

from flask import request
from flask_restx import Resource
from pydantic import BaseModel, Field

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from extensions.ext_database import db
from libs.helper import email as validate_email
from models.beta_application import BetaApplication
from services.beta_application_notification_service import BetaApplicationNotificationService

DEFAULT_REF_TEMPLATE_SWAGGER_2_0 = "#/definitions/{model}"
BLOCK_DUPLICATE_STATUSES = ("pending", "provisioning", "success")


class ApplyBetaPayload(BaseModel):
    email: str = Field(..., description="Email address")
    name: str = Field(..., description="User name")
    company: str | None = Field(default=None, description="Company name")
    use_case: str | None = Field(default=None, description="Use case description")
    language: str | None = Field(default=None, description="Interface language")


def reg(cls: type[BaseModel]):
    console_ns.schema_model(cls.__name__, cls.model_json_schema(ref_template=DEFAULT_REF_TEMPLATE_SWAGGER_2_0))


reg(ApplyBetaPayload)


def submit_beta_application(*, args: ApplyBetaPayload, remote_addr: str | None, user_agent: str | None):
    request_email = args.email
    normalized_email = request_email.lower()
    name = args.name
    company = args.company
    use_case = args.use_case
    language = args.language or "zh-Hans"

    # Validate email format
    try:
        validate_email(normalized_email)
    except ValueError as e:
        return {"result": "fail", "data": str(e)}, 400

    # Duplicate check for active applications
    try:
        existing_application = (
            db.session.query(BetaApplication)
            .filter(
                BetaApplication.email == normalized_email,
                BetaApplication.status.in_(BLOCK_DUPLICATE_STATUSES),
            )
            .first()
        )
        if existing_application:
            return {
                "result": "fail",
                "data": "This email has already submitted a beta application.",
            }, 400

        beta_app = BetaApplication(
            id=str(uuid4()),
            email=normalized_email,
            name=name,
            language=language,
            company=company,
            use_case=use_case,
            status="pending",
            ip_address=remote_addr,
            user_agent=(user_agent or "")[:500],
        )
        db.session.add(beta_app)
        db.session.commit()
        BetaApplicationNotificationService.send_submitted_email(
            application_id=beta_app.id,
            to=beta_app.email,
            name=beta_app.name,
            language=language,
        )

        return {
            "result": "success",
            "data": "Application submitted successfully. Please wait for administrator review.",
            "application_id": beta_app.id,
            "status": beta_app.status,
        }, 201
    except Exception as db_error:
        db.session.rollback()
        return {"result": "fail", "data": f"Application failed: {str(db_error)}"}, 400


@console_ns.route("/apply-beta")
class ApplyBetaApi(Resource):
    """Resource for beta application."""

    @setup_required
    @console_ns.expect(console_ns.models[ApplyBetaPayload.__name__])
    def post(self):
        """Submit beta application."""
        args = ApplyBetaPayload.model_validate(console_ns.payload)
        return submit_beta_application(
            args=args,
            remote_addr=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
