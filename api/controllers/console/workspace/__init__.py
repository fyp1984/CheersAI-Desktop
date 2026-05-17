from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from sqlalchemy.orm import Session
from werkzeug.exceptions import Forbidden

from extensions.ext_database import db
from libs.desktop_auth import DESKTOP_AGENT_MANAGE_CAPABILITY, DESKTOP_PLUGIN_MANAGE_CAPABILITY, DESKTOP_SYSTEM_ADMIN_CAPABILITY
from libs.login import current_account_with_tenant
from models.account import TenantPluginPermission

P = ParamSpec("P")
R = TypeVar("R")


def _require_workspace_capabilities(*capabilities: str):
    from controllers.console.wraps import require_workspace_capabilities

    return require_workspace_capabilities(*capabilities)


def require_plugin_manage_capability(view: Callable[P, R]):
    return _require_workspace_capabilities(DESKTOP_PLUGIN_MANAGE_CAPABILITY, "desktop_api_extension_manage")(view)


def require_system_admin_plugin_install_capability(view: Callable[P, R]):
    @wraps(view)
    def decorated(*args: P.args, **kwargs: P.kwargs):
        user, _ = current_account_with_tenant()
        owner = ""
        custom_config = getattr(user, "custom_config_dict", None)
        if isinstance(custom_config, dict):
            owner = (custom_config.get("desktop_sso_owner") or "").strip().lower()
        if owner != "built-in":
            raise Forbidden("请联系系统管理员进行安装")

        return view(*args, **kwargs)

    return decorated


def require_team_manage_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_team_manage")(view)


def require_member_manage_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_member_manage", "desktop_team_manage")(view)


def require_workspace_settings_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_settings_team")(view)


def require_model_provider_manage_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_model_provider_manage", "desktop_model_manage")(view)


def require_data_source_manage_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_data_source_manage")(view)


def require_api_extension_manage_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_api_extension_manage", DESKTOP_PLUGIN_MANAGE_CAPABILITY)(view)


def require_data_security_manage_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_data_security_manage", "desktop_settings_team")(view)


def require_language_manage_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_language_manage")(view)


def require_chat_use_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_chat_use")(view)


def require_app_view_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_app_view")(view)


def require_app_run_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_app_run")(view)


def require_app_edit_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_app_edit")(view)


def require_explore_view_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_explore_view")(view)


def require_audit_view_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_audit_view")(view)


def require_knowledge_view_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_knowledge_view")(view)


def require_knowledge_edit_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_knowledge_edit")(view)


def require_workflow_view_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_workflow_view")(view)


def require_workflow_edit_capability(view: Callable[P, R]):
    return _require_workspace_capabilities("desktop_workflow_edit")(view)


def plugin_permission_required(
    install_required: bool = False,
    debug_required: bool = False,
):
    def interceptor(view: Callable[P, R]):
        @wraps(view)
        def decorated(*args: P.args, **kwargs: P.kwargs):
            current_user, current_tenant_id = current_account_with_tenant()
            user = current_user
            tenant_id = current_tenant_id

            with Session(db.engine) as session:
                permission = (
                    session.query(TenantPluginPermission)
                    .where(
                        TenantPluginPermission.tenant_id == tenant_id,
                    )
                    .first()
                )

                if not permission:
                    # no permission set, allow access for everyone
                    return view(*args, **kwargs)

                if install_required:
                    if permission.install_permission == TenantPluginPermission.InstallPermission.NOBODY:
                        raise Forbidden()
                    if permission.install_permission == TenantPluginPermission.InstallPermission.ADMINS:
                        if not user.is_admin_or_owner:
                            raise Forbidden()
                    if permission.install_permission == TenantPluginPermission.InstallPermission.EVERYONE:
                        pass

                if debug_required:
                    if permission.debug_permission == TenantPluginPermission.DebugPermission.NOBODY:
                        raise Forbidden()
                    if permission.debug_permission == TenantPluginPermission.DebugPermission.ADMINS:
                        if not user.is_admin_or_owner:
                            raise Forbidden()
                    if permission.debug_permission == TenantPluginPermission.DebugPermission.EVERYONE:
                        pass

            return view(*args, **kwargs)

        return decorated

    return interceptor
