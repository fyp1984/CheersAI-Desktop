import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from extensions.ext_redis import redis_client
from models.account import TenantAccountRole

DESKTOP_ACCESS_CAPABILITY = "desktop_access"
DESKTOP_AGENT_MANAGE_CAPABILITY = "desktop_agent_manage"
DESKTOP_PLUGIN_MANAGE_CAPABILITY = "desktop_plugin_manage"
DESKTOP_SSO_PROJECTION_KEY_PREFIX = "desktop:sso:projection"
DESKTOP_SSO_PROJECTION_TTL = 60 * 60 * 24 * 7

WORKSPACE_ROLE_CAPABILITIES: dict[str, frozenset[str]] = {
    TenantAccountRole.OWNER: frozenset({
        "desktop_access",
        "desktop_model_use",
        "desktop_agent_use",
        "desktop_agent_test",
        "desktop_agent_view",
        "desktop_agent_run",
        DESKTOP_AGENT_MANAGE_CAPABILITY,
        DESKTOP_PLUGIN_MANAGE_CAPABILITY,
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_knowledge_edit",
        "desktop_workflow_view",
        "desktop_workflow_run",
        "desktop_workflow_edit",
        "desktop_app_view",
        "desktop_app_run",
        "desktop_app_edit",
        "desktop_explore_view",
        "desktop_settings_personal",
        "desktop_settings_team",
        "desktop_team_manage",
        "desktop_audit_view",
        "desktop_model_manage",
        "desktop_model_provider_manage",
        "desktop_member_manage",
        "desktop_data_source_manage",
        "desktop_api_extension_manage",
        "desktop_data_security_manage",
        "desktop_language_manage",
    }),
    TenantAccountRole.ADMIN: frozenset({
        "desktop_access",
        "desktop_model_use",
        "desktop_agent_use",
        "desktop_agent_test",
        "desktop_agent_view",
        "desktop_agent_run",
        DESKTOP_AGENT_MANAGE_CAPABILITY,
        DESKTOP_PLUGIN_MANAGE_CAPABILITY,
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_knowledge_edit",
        "desktop_workflow_view",
        "desktop_workflow_run",
        "desktop_workflow_edit",
        "desktop_app_view",
        "desktop_app_run",
        "desktop_app_edit",
        "desktop_explore_view",
        "desktop_settings_personal",
        "desktop_settings_team",
        "desktop_team_manage",
        "desktop_audit_view",
        "desktop_model_manage",
        "desktop_model_provider_manage",
        "desktop_member_manage",
        "desktop_data_source_manage",
        "desktop_api_extension_manage",
        "desktop_data_security_manage",
        "desktop_language_manage",
    }),
    TenantAccountRole.EDITOR: frozenset({
        "desktop_access",
        "desktop_model_use",
        "desktop_agent_use",
        "desktop_agent_test",
        "desktop_agent_view",
        "desktop_agent_run",
        DESKTOP_AGENT_MANAGE_CAPABILITY,
        DESKTOP_PLUGIN_MANAGE_CAPABILITY,
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_knowledge_edit",
        "desktop_workflow_view",
        "desktop_workflow_run",
        "desktop_workflow_edit",
        "desktop_app_view",
        "desktop_app_run",
        "desktop_app_edit",
        "desktop_explore_view",
        "desktop_settings_personal",
        "desktop_model_manage",
        "desktop_model_provider_manage",
        "desktop_data_source_manage",
        "desktop_language_manage",
    }),
    TenantAccountRole.NORMAL: frozenset({
        "desktop_access",
        "desktop_model_use",
        "desktop_agent_use",
        "desktop_agent_view",
        "desktop_agent_run",
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_workflow_view",
        "desktop_workflow_run",
        "desktop_app_view",
        "desktop_app_run",
        "desktop_explore_view",
        "desktop_settings_personal",
        "desktop_language_manage",
    }),
    TenantAccountRole.DATASET_OPERATOR: frozenset({
        "desktop_access",
        "desktop_model_use",
        "desktop_agent_use",
        "desktop_agent_test",
        "desktop_agent_view",
        "desktop_agent_run",
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_knowledge_edit",
        "desktop_workflow_view",
        "desktop_workflow_run",
        "desktop_app_view",
        "desktop_app_run",
        "desktop_explore_view",
        "desktop_settings_personal",
        "desktop_language_manage",
    }),
}

SSO_IDENTIFIER_TO_WORKSPACE_ROLE: dict[str, str] = {
    "owner": TenantAccountRole.OWNER,
    "admin": TenantAccountRole.ADMIN,
    "c_admin": TenantAccountRole.ADMIN,
    "desktop_team_admin": TenantAccountRole.ADMIN,
    "org_admin": TenantAccountRole.ADMIN,
    "desktop_bundle_admin": TenantAccountRole.ADMIN,
    "permission_cheersai_admin": TenantAccountRole.ADMIN,
    "permission_cheersal_admin": TenantAccountRole.ADMIN,
    "technician": TenantAccountRole.EDITOR,
    "editor": TenantAccountRole.EDITOR,
    "desktop_team_editor": TenantAccountRole.EDITOR,
    "agent-edit": TenantAccountRole.EDITOR,
    "desktop_bundle_editor": TenantAccountRole.EDITOR,
    "permission_cheersai_edit": TenantAccountRole.EDITOR,
    "permission_cheersal_edit": TenantAccountRole.EDITOR,
    "dataset_operator": TenantAccountRole.DATASET_OPERATOR,
    "desktop_dataset_operator": TenantAccountRole.DATASET_OPERATOR,
    "desktop_bundle_dataset_operator": TenantAccountRole.DATASET_OPERATOR,
    "user": TenantAccountRole.NORMAL,
    "normal": TenantAccountRole.NORMAL,
    "desktop_team_member": TenantAccountRole.NORMAL,
    "team-member": TenantAccountRole.NORMAL,
    "desktop_bundle_member": TenantAccountRole.NORMAL,
    "permission_cheersai_member": TenantAccountRole.NORMAL,
    "permission_cheersal_member": TenantAccountRole.NORMAL,
}

WORKSPACE_ROLE_PRIORITY: dict[str, int] = {
    TenantAccountRole.NORMAL: 1,
    TenantAccountRole.DATASET_OPERATOR: 2,
    TenantAccountRole.EDITOR: 3,
    TenantAccountRole.ADMIN: 4,
    TenantAccountRole.OWNER: 5,
}

STANDARD_CAPABILITIES = frozenset({
    capability
    for capabilities in WORKSPACE_ROLE_CAPABILITIES.values()
    for capability in capabilities
})


def normalize_sso_identifier(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    if not normalized:
        return None

    normalized = normalized.split("/")[-1]
    return normalized.replace(" ", "_")


def collect_sso_identifiers(payload: Mapping[str, Any] | None) -> list[str]:
    if not payload:
        return []

    identifiers: list[str] = []

    for key in ("roles", "permissions"):
        values = payload.get(key)
        if isinstance(values, Iterable) and not isinstance(values, (str, bytes)):
            for value in values:
                normalized = normalize_sso_identifier(value)
                if normalized:
                    identifiers.append(normalized)

    for key in ("role", "type"):
        normalized = normalize_sso_identifier(payload.get(key))
        if normalized:
            identifiers.append(normalized)

    return list(dict.fromkeys(identifiers))


def has_desktop_access(payload: Mapping[str, Any] | None) -> bool:
    # Allow access if user has desktop_access capability
    if DESKTOP_ACCESS_CAPABILITY in collect_sso_identifiers(payload):
        return True
    
    # Auto-grant desktop_access to users with valid SSO roles
    identifiers = collect_sso_identifiers(payload)
    for identifier in identifiers:
        if identifier in SSO_IDENTIFIER_TO_WORKSPACE_ROLE:
            return True
    
    # Auto-grant desktop_access to all valid SSO users (with email and sub)
    # This allows users without explicit roles to access the system
    if payload and payload.get('sub') and payload.get('email'):
        return True
    
    return False


def resolve_workspace_role(payload: Mapping[str, Any] | None) -> tuple[str | None, str]:
    identifiers = collect_sso_identifiers(payload)
    resolved_identifier: str | None = None
    resolved_workspace_role = TenantAccountRole.NORMAL
    resolved_priority = WORKSPACE_ROLE_PRIORITY[resolved_workspace_role]

    for identifier in identifiers:
        workspace_role = SSO_IDENTIFIER_TO_WORKSPACE_ROLE.get(identifier)
        if not workspace_role:
            continue

        workspace_priority = WORKSPACE_ROLE_PRIORITY.get(workspace_role, 0)
        if workspace_priority > resolved_priority:
            resolved_identifier = identifier
            resolved_workspace_role = workspace_role
            resolved_priority = workspace_priority

    return resolved_identifier, resolved_workspace_role


def get_role_capabilities(role: str | None) -> list[str]:
    if not role:
        return []

    try:
        normalized_role = TenantAccountRole(role)
    except ValueError:
        return []

    return list(WORKSPACE_ROLE_CAPABILITIES.get(normalized_role, frozenset()))


def resolve_workspace_capabilities(payload: Mapping[str, Any] | None, fallback_role: str | None = None) -> list[str]:
    identifiers = collect_sso_identifiers(payload)
    capabilities: set[str] = set()

    for identifier in identifiers:
        if identifier in STANDARD_CAPABILITIES:
            capabilities.add(identifier)
            continue

        mapped_role = SSO_IDENTIFIER_TO_WORKSPACE_ROLE.get(identifier)
        if mapped_role:
            capabilities.update(get_role_capabilities(mapped_role))

    if fallback_role:
        capabilities.update(get_role_capabilities(fallback_role))

    if has_desktop_access(payload):
        capabilities.add(DESKTOP_ACCESS_CAPABILITY)

    return sorted(capabilities)


def build_desktop_sso_projection(
    payload: Mapping[str, Any] | None,
    *,
    workspace_role: str | None,
    mapped_role: str | None,
) -> dict[str, Any]:
    normalized_roles = [
        normalized
        for value in payload.get("roles", []) if payload and isinstance(payload.get("roles"), Iterable) and not isinstance(payload.get("roles"), (str, bytes))
        for normalized in [normalize_sso_identifier(value)]
        if normalized
    ]
    normalized_permissions = [
        normalized
        for value in payload.get("permissions", []) if payload and isinstance(payload.get("permissions"), Iterable) and not isinstance(payload.get("permissions"), (str, bytes))
        for normalized in [normalize_sso_identifier(value)]
        if normalized
    ]
    capabilities = resolve_workspace_capabilities(payload, workspace_role)
    sync_hash_source = "|".join([
        *(normalized_roles or []),
        *(normalized_permissions or []),
        *(capabilities or []),
        workspace_role or "",
        mapped_role or "",
    ])

    return {
        "workspace_role": workspace_role,
        "mapped_role": mapped_role,
        "roles": normalized_roles,
        "permissions": normalized_permissions,
        "capabilities": capabilities,
        "sync_hash": hashlib.sha256(sync_hash_source.encode("utf-8")).hexdigest(),
    }


def _desktop_sso_projection_key(account_id: str, tenant_id: str) -> str:
    return f"{DESKTOP_SSO_PROJECTION_KEY_PREFIX}:{tenant_id}:{account_id}"


def save_desktop_sso_projection(account_id: str, tenant_id: str, projection: Mapping[str, Any]) -> None:
    try:
        redis_client.set(
            _desktop_sso_projection_key(account_id, tenant_id),
            json.dumps(dict(projection)).encode("utf-8"),
            ex=DESKTOP_SSO_PROJECTION_TTL,
        )
    except RuntimeError:
        return


def load_desktop_sso_projection(account_id: str, tenant_id: str) -> dict[str, Any] | None:
    try:
        projection = redis_client.get(_desktop_sso_projection_key(account_id, tenant_id))
    except RuntimeError:
        return None

    if not projection:
        return None

    if isinstance(projection, bytes):
        projection = projection.decode("utf-8")

    try:
        loaded_projection = json.loads(projection)
    except json.JSONDecodeError:
        return None

    if not isinstance(loaded_projection, dict):
        return None

    return loaded_projection


def get_current_workspace_role(account: Any) -> str | None:
    for attr in ("current_role", "current_tenant_current_role", "role"):
        value = getattr(account, attr, None)
        if value:
            return str(value)
    return None


def get_account_workspace_capabilities(account: Any, tenant_id: str | None = None) -> list[str]:
    capabilities: set[str] = set()
    account_id = getattr(account, "id", None)
    resolved_tenant_id = tenant_id or getattr(account, "current_tenant_id", None)

    if isinstance(account_id, str) and resolved_tenant_id:
        projection = load_desktop_sso_projection(account_id, str(resolved_tenant_id))
        if projection:
            projection_capabilities = projection.get("capabilities")
            if isinstance(projection_capabilities, list):
                capabilities.update(capability for capability in projection_capabilities if isinstance(capability, str))

    capabilities.update(get_role_capabilities(get_current_workspace_role(account)))
    return sorted(capabilities)


def has_any_workspace_capability(account: Any, capabilities: Iterable[str], tenant_id: str | None = None) -> bool:
    capability_set = set(get_account_workspace_capabilities(account, tenant_id))
    return any(capability in capability_set for capability in capabilities)


def has_role_capability(role: str | None, capability: str) -> bool:
    return capability in WORKSPACE_ROLE_CAPABILITIES.get(role or "", frozenset())
