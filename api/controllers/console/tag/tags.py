from typing import Literal
from uuid import UUID

from flask import request
from flask_restx import Resource
from pydantic import BaseModel, Field
from werkzeug.exceptions import Forbidden, NotFound

from controllers.console import console_ns
from controllers.console.wraps import account_initialization_required, setup_required
from libs.desktop_auth import has_any_workspace_capability
from libs.login import current_account_with_tenant, login_required
from services.tag_service import TagService


class TagBasePayload(BaseModel):
    name: str = Field(description="Tag name", min_length=1, max_length=50)
    type: Literal["knowledge", "app"] | None = Field(default=None, description="Tag type")


class TagBindingPayload(BaseModel):
    tag_ids: list[str] = Field(description="Tag IDs to bind")
    target_id: str = Field(description="Target ID to bind tags to")
    type: Literal["knowledge", "app"] | None = Field(default=None, description="Tag type")


class TagBindingRemovePayload(BaseModel):
    tag_id: str = Field(description="Tag ID to remove")
    target_id: str = Field(description="Target ID to unbind tag from")
    type: Literal["knowledge", "app"] | None = Field(default=None, description="Tag type")


class TagListQueryParam(BaseModel):
    type: Literal["knowledge", "app", ""] = Field("", description="Tag type filter")
    keyword: str | None = Field(None, description="Search keyword")


class TagResponse(BaseModel):
    id: str = Field(description="Tag ID")
    name: str = Field(description="Tag name")
    type: str = Field(description="Tag type")
    binding_count: int = Field(description="Number of bindings")


class TagBindingResult(BaseModel):
    result: Literal["success"] = Field(description="Operation result", examples=["success"])


TAG_TYPE_MANAGE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "app": ("desktop_app_edit",),
    "knowledge": ("desktop_knowledge_edit",),
}


def _ensure_tag_manage_permission(tag_type: Literal["knowledge", "app"] | None) -> None:
    current_user, current_tenant_id = current_account_with_tenant()
    capabilities = TAG_TYPE_MANAGE_CAPABILITIES.get(tag_type or "", ("desktop_agent_manage", "desktop_knowledge_edit"))
    if not has_any_workspace_capability(current_user, capabilities, current_tenant_id):
        raise Forbidden()


@console_ns.route("/tags")
class TagListApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self):
        query = TagListQueryParam.model_validate(request.args.to_dict())
        _, current_tenant_id = current_account_with_tenant()
        tags = TagService.get_tags(query.type, current_tenant_id, query.keyword)

        return [
            TagResponse(
                id=tag.id,
                name=tag.name,
                type=tag.type,
                binding_count=int(tag.binding_count),
            ).model_dump()
            for tag in tags
        ]

    @setup_required
    @login_required
    @account_initialization_required
    def post(self):
        payload = TagBasePayload.model_validate(request.get_json(silent=True) or {})
        _ensure_tag_manage_permission(payload.type)

        tag = TagService.save_tags(payload.model_dump())

        return TagResponse(id=tag.id, name=tag.name, type=tag.type, binding_count=0).model_dump(), 201


@console_ns.route("/tags/<uuid:tag_id>")
class TagApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def patch(self, tag_id: UUID):
        payload = TagBasePayload.model_validate(request.get_json(silent=True) or {})
        tag_id_str = str(tag_id)
        _ensure_tag_manage_permission(payload.type)

        tag = TagService.update_tags(payload.model_dump(), tag_id_str)
        binding_count = TagService.get_tag_binding_count(tag_id_str)

        return TagResponse(id=tag.id, name=tag.name, type=tag.type, binding_count=binding_count).model_dump()

    @setup_required
    @login_required
    @account_initialization_required
    def delete(self, tag_id: UUID):
        tag_id_str = str(tag_id)
        tag = TagService.get_tag(tag_id_str)
        if not tag:
            raise NotFound("Tag not found")
        _ensure_tag_manage_permission(tag.type)

        TagService.delete_tag(tag_id_str)
        return "", 204


@console_ns.route("/tag-bindings/create")
class TagBindingCreateApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self):
        payload = TagBindingPayload.model_validate(request.get_json(silent=True) or {})
        _ensure_tag_manage_permission(payload.type)

        TagService.save_tag_binding(payload.model_dump())

        return TagBindingResult(result="success").model_dump()


@console_ns.route("/tag-bindings/remove")
class TagBindingRemoveApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self):
        payload = TagBindingRemovePayload.model_validate(request.get_json(silent=True) or {})
        _ensure_tag_manage_permission(payload.type)

        TagService.delete_tag_binding(payload.model_dump())

        return TagBindingResult(result="success").model_dump()
