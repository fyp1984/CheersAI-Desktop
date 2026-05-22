from functools import wraps
from typing import Any

from flask_restx import Resource
from pydantic import BaseModel, Field
from sqlalchemy import select
from werkzeug.exceptions import Forbidden

from controllers.console import console_ns
from controllers.console.app.wraps import get_app_model
from controllers.console.wraps import account_initialization_required, setup_required
from extensions.ext_database import db
from libs.datetime_utils import naive_utc_now
from libs.login import current_user, login_required
from models import Account, App, AppInstruction


class AppInstructionUpdatePayload(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str = Field(default="", max_length=200_000)
    source_file_name: str | None = Field(default=None, max_length=255)
    source_file_size: int | None = Field(default=None, ge=0)


def _serialize_instruction(instruction: AppInstruction | None) -> dict[str, Any] | None:
    if instruction is None:
        return None
    return {
        "id": instruction.id,
        "tenant_id": instruction.tenant_id,
        "app_id": instruction.app_id,
        "title": instruction.title,
        "content": instruction.content,
        "source_file_name": instruction.source_file_name,
        "source_file_size": instruction.source_file_size,
        "created_by": instruction.created_by,
        "created_at": int(instruction.created_at.timestamp()) if instruction.created_at else None,
        "updated_by": instruction.updated_by,
        "updated_at": int(instruction.updated_at.timestamp()) if instruction.updated_at else None,
    }


def _get_instruction(app_id: str) -> AppInstruction | None:
    return db.session.scalar(select(AppInstruction).where(AppInstruction.app_id == app_id))


def instruction_manage_permission_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if not isinstance(current_user, Account):
            raise Forbidden()
        if not (current_user.is_admin_or_owner or current_user.has_edit_permission):
            raise Forbidden()
        return view(*args, **kwargs)

    return decorated


@console_ns.route("/apps/<uuid:app_id>/instruction")
class AppInstructionApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model
    def get(self, app_model: App):
        instruction = _get_instruction(app_model.id)
        return {"instruction": _serialize_instruction(instruction)}

    @setup_required
    @login_required
    @account_initialization_required
    @instruction_manage_permission_required
    @get_app_model
    def post(self, app_model: App):
        payload = AppInstructionUpdatePayload.model_validate(console_ns.payload or {})
        if not isinstance(current_user, Account):
            raise Forbidden()

        instruction = _get_instruction(app_model.id)
        now = naive_utc_now()
        title = payload.title or payload.source_file_name or "使用说明"
        if instruction is None:
            instruction = AppInstruction(
                tenant_id=app_model.tenant_id,
                app_id=app_model.id,
                title=title,
                content=payload.content,
                source_file_name=payload.source_file_name,
                source_file_size=payload.source_file_size or 0,
                created_by=current_user.id,
                updated_by=current_user.id,
                created_at=now,
                updated_at=now,
            )
            db.session.add(instruction)
        else:
            instruction.title = title
            instruction.content = payload.content
            instruction.source_file_name = payload.source_file_name
            instruction.source_file_size = payload.source_file_size or 0
            instruction.updated_by = current_user.id
            instruction.updated_at = now

        db.session.commit()
        return {"instruction": _serialize_instruction(instruction)}

    @setup_required
    @login_required
    @account_initialization_required
    @instruction_manage_permission_required
    @get_app_model
    def delete(self, app_model: App):
        instruction = _get_instruction(app_model.id)
        if instruction is not None:
            db.session.delete(instruction)
            db.session.commit()
        return {"result": "success"}
