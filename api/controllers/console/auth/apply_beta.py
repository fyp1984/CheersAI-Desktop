from uuid import uuid4

from flask import request
from flask_restx import Resource
from pydantic import BaseModel, Field

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from libs.helper import email as validate_email
from models.account import AccountStatus
from models.beta_application import BetaApplication
from services.account_service import RegisterService
from extensions.ext_database import db
from utils.sqlite_helper import SQLiteHelper

DEFAULT_REF_TEMPLATE_SWAGGER_2_0 = "#/definitions/{model}"


class ApplyBetaPayload(BaseModel):
    email: str = Field(..., description="Email address")
    name: str = Field(..., description="User name")
    company: str | None = Field(default=None, description="Company name")
    use_case: str | None = Field(default=None, description="Use case description")
    language: str | None = Field(default=None, description="Interface language")


def reg(cls: type[BaseModel]):
    console_ns.schema_model(cls.__name__, cls.model_json_schema(ref_template=DEFAULT_REF_TEMPLATE_SWAGGER_2_0))


reg(ApplyBetaPayload)


@console_ns.route("/apply-beta")
class ApplyBetaApi(Resource):
    """Resource for beta application."""

    @setup_required
    @console_ns.expect(console_ns.models[ApplyBetaPayload.__name__])
    def post(self):
        """Submit beta application."""
        args = ApplyBetaPayload.model_validate(console_ns.payload)
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

        # Get client info
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")

        # Check if email already applied
        existing_application = db.session.query(BetaApplication).filter_by(email=normalized_email).first()
        if existing_application:
            return {
                "result": "fail",
                "data": "This email has already submitted a beta application.",
            }, 400

        # Save beta application to PostgreSQL database
        try:
            beta_app = BetaApplication(
                id=str(uuid4()),
                email=normalized_email,
                name=name,
                company=company,
                use_case=use_case,
                status="pending",
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else None,
            )
            db.session.add(beta_app)
            db.session.commit()

            # Also save to SQLite database
            try:
                sqlite_helper = SQLiteHelper()
                sqlite_helper.save_beta_application(
                    email=normalized_email,
                    name=name,
                    company=company,
                    use_case=use_case,
                    status="pending",
                    ip_address=ip_address,
                    user_agent=user_agent[:500] if user_agent else None,
                )
            except Exception as sqlite_error:
                # Log SQLite error but don't fail the request
                print(f"SQLite save failed: {sqlite_error}")

            # Also create account with PENDING status
            try:
                account = RegisterService.register(
                    email=normalized_email,
                    name=name,
                    language=language,
                    status=AccountStatus.PENDING,
                    is_setup=True,
                    create_workspace_required=False,
                )
            except Exception as e:
                # If account creation fails, it's okay - we still have the beta application record
                pass

            return {
                "result": "success",
                "data": "Application submitted successfully. Please wait for administrator review.",
            }, 201
        except Exception as e:
            db.session.rollback()
            error_message = str(e)
            return {"result": "fail", "data": f"Application failed: {error_message}"}, 400
