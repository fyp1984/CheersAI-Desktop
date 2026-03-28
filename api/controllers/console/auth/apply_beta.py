from uuid import uuid4
import os
import requests

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

# SSO API 配置
SSO_API_URL = os.getenv("SSO_API_URL", "http://localhost:8000/api")


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

        # 调用 SSO API 提交申请
        try:
            sso_response = requests.post(
                f"{SSO_API_URL}/apply-beta",
                data={
                    "email": normalized_email,
                    "name": name,
                    "company": company or "",
                    "useCase": use_case or "",
                },
                timeout=10,
            )

            if sso_response.status_code == 200:
                # SSO API 调用成功，同时保存到本地 SQLite 作为备份
                try:
                    sqlite_helper = SQLiteHelper()
                    sqlite_helper.save_beta_application(
                        email=normalized_email,
                        name=name,
                        company=company,
                        use_case=use_case,
                        status="pending",
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get("User-Agent", "")[:500],
                    )
                except Exception as sqlite_error:
                    print(f"SQLite backup save failed: {sqlite_error}")

                return {
                    "result": "success",
                    "data": "Application submitted successfully. Please wait for administrator review.",
                }, 201
            else:
                # SSO API 返回错误
                error_data = sso_response.json() if sso_response.headers.get("content-type") == "application/json" else {}
                error_message = error_data.get("msg", "Failed to submit application to SSO")
                
                # 如果是邮箱已存在错误，返回特定消息
                if "already" in error_message.lower():
                    return {
                        "result": "fail",
                        "data": "This email has already submitted a beta application.",
                    }, 400
                
                return {"result": "fail", "data": error_message}, 400

        except requests.exceptions.RequestException as e:
            # 网络错误，降级到本地数据库
            print(f"SSO API call failed, falling back to local database: {e}")
            
            # 检查本地数据库是否已存在
            existing_application = db.session.query(BetaApplication).filter_by(email=normalized_email).first()
            if existing_application:
                return {
                    "result": "fail",
                    "data": "This email has already submitted a beta application.",
                }, 400

            # 保存到本地 PostgreSQL 数据库
            try:
                beta_app = BetaApplication(
                    id=str(uuid4()),
                    email=normalized_email,
                    name=name,
                    company=company,
                    use_case=use_case,
                    status="pending",
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get("User-Agent", "")[:500],
                )
                db.session.add(beta_app)
                db.session.commit()

                return {
                    "result": "success",
                    "data": "Application submitted successfully. Please wait for administrator review.",
                }, 201
            except Exception as db_error:
                db.session.rollback()
                return {"result": "fail", "data": f"Application failed: {str(db_error)}"}, 400
