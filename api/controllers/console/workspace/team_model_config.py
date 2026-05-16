import hashlib

from flask import request
from flask_restx import Resource
from pydantic import BaseModel, Field

from controllers.common.schema import register_schema_models
from controllers.console import console_ns
from controllers.console.workspace import require_model_provider_manage_capability
from controllers.console.wraps import (
    account_initialization_required,
    require_workspace_capabilities,
    setup_required,
)
from core.model_runtime.entities.model_entities import ModelType
from core.model_runtime.utils.encoders import jsonable_encoder
from libs.desktop_auth import DESKTOP_SYSTEM_ADMIN_CAPABILITY
from libs.login import current_account_with_tenant, login_required
from services.model_provider_service import ModelProviderService
from services.plugin.plugin_service import PluginService
from services.team_model_config_service import TeamModelConfigService


class AdminPluginInstallPayload(BaseModel):
    md5: str | None = None


class TeamModelConfigPayload(BaseModel):
    plugin_code: str
    api_key: str | None = None
    base_url: str = Field(min_length=1)
    max_concurrent: int | None = Field(default=None, ge=1)
    max_qps: int | None = Field(default=None, ge=1)


class ModelListQuery(BaseModel):
    model_type: ModelType = ModelType.LLM


register_schema_models(console_ns, AdminPluginInstallPayload, TeamModelConfigPayload, ModelListQuery)


@console_ns.route("/admin/plugin/install")
class GlobalPluginInstallApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @require_workspace_capabilities(DESKTOP_SYSTEM_ADMIN_CAPABILITY)
    def post(self):
        current_account, tenant_id = current_account_with_tenant()
        file = request.files.get("pkg") or request.files.get("jar")
        if not file:
            raise ValueError("pkg file is required")

        content = file.read()
        md5 = request.form.get("md5")
        if md5:
            actual_md5 = hashlib.md5(content).hexdigest()
            if actual_md5.lower() != md5.lower():
                raise ValueError("MD5 verification failed")

        upload_response = PluginService.upload_pkg(tenant_id, content)
        install_response = PluginService.install_from_local_pkg(tenant_id, [upload_response.unique_identifier])

        return jsonable_encoder(
            {
                "result": "success",
                "message": "插件安装任务已创建，安装完成后将自动共享给所有团队",
                "task": install_response,
                "plugin_unique_identifier": upload_response.unique_identifier,
            }
        )


@console_ns.route("/team/model-config")
class TeamModelConfigApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @require_model_provider_manage_capability
    def get(self):
        _, tenant_id = current_account_with_tenant()
        return jsonable_encoder({"data": TeamModelConfigService.list_team_model_configs(tenant_id)})

    @setup_required
    @login_required
    @account_initialization_required
    @require_model_provider_manage_capability
    def post(self):
        current_account, tenant_id = current_account_with_tenant()
        payload = TeamModelConfigPayload.model_validate(console_ns.payload or {})
        result = TeamModelConfigService.save_team_model_config(
            team_id=tenant_id,
            updated_by=current_account.id,
            plugin_code=payload.plugin_code,
            api_key=payload.api_key,
            base_url=payload.base_url,
            max_concurrent=payload.max_concurrent,
            max_qps=payload.max_qps,
        )
        return jsonable_encoder({"result": "success", "data": result})


@console_ns.route("/model/list")
class TeamAvailableModelListApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self):
        _, tenant_id = current_account_with_tenant()
        args = ModelListQuery.model_validate(request.args.to_dict(flat=True))  # type: ignore[arg-type]
        service = ModelProviderService()
        return jsonable_encoder({"data": service.get_models_by_model_type(tenant_id, args.model_type)})
