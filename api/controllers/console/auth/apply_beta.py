from flask_restx import Resource
from pydantic import BaseModel, Field

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from libs.helper import email as validate_email
from models.account import AccountStatus
from services.account_service import RegisterService

DEFAULT_REF_TEMPLATE_SWAGGER_2_0 = "#/definitions/{model}"


class ApplyBetaPayload(BaseModel):
    email: str = Field(..., description="Email address")
    name: str = Field(..., description="User name")
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
        language = args.language or "zh-Hans"

        # Validate email format
        try:
            validate_email(normalized_email)
        except ValueError as e:
            return {"result": "fail", "data": str(e)}, 400

        # Create account with PENDING status
        try:
            account = RegisterService.register(
                email=normalized_email,
                name=name,
                language=language,
                status=AccountStatus.PENDING,
                is_setup=True,
                create_workspace_required=False,
            )

            return {
                "result": "success",
                "data": "Application submitted successfully. Please wait for administrator review.",
            }, 201
        except Exception as e:
            error_message = str(e)
            if "already exists" in error_message.lower() or "duplicate" in error_message.lower():
                return {
                    "result": "fail",
                    "data": "This email has already been registered or applied.",
                }, 400
            return {"result": "fail", "data": f"Application failed: {error_message}"}, 400
