import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from extensions.ext_database import db
from extensions.ext_redis import redis_client
from models.account import Account, Tenant, TenantAccountJoin, TenantAccountRole, TenantStatus

DESKTOP_ACCESS_CAPABILITY = "desktop_access"
DESKTOP_AGENT_MANAGE_CAPABILITY = "desktop_agent_manage"
DESKTOP_PLUGIN_MANAGE_CAPABILITY = "desktop_plugin_manage"
DESKTOP_SSO_PROJECTION_KEY_PREFIX = "desktop:sso:projection"
DESKTOP_SSO_GROUP_TENANT_CACHE_PREFIX = "desktop:sso:group-tenant:"
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

ADMIN_TAG_KEYWORDS = ("admin", "管理员")


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


def is_admin_like_tag(tag: Any) -> bool:
    if not isinstance(tag, str):
        return False

    normalized = tag.strip().lower()
    if not normalized:
        return False

    return any(keyword in normalized for keyword in ADMIN_TAG_KEYWORDS)


def has_admin_tag_override(user_tags: Iterable[str] | None) -> bool:
    return any(is_admin_like_tag(tag) for tag in user_tags or [])


def get_admin_override_capabilities(user_tags: Iterable[str] | None) -> list[str]:
    if not has_admin_tag_override(user_tags):
        return []

    return get_role_capabilities(TenantAccountRole.ADMIN)


def resolve_workspace_capabilities(
    payload: Mapping[str, Any] | None,
    fallback_role: str | None = None,
    sso_tags: Iterable[str] | None = None,
) -> list[str]:
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

    capabilities.update(get_admin_override_capabilities(sso_tags))

    if has_desktop_access(payload):
        capabilities.add(DESKTOP_ACCESS_CAPABILITY)

    return sorted(capabilities)


def build_desktop_sso_projection(
    payload: Mapping[str, Any] | None,
    *,
    workspace_role: str | None,
    mapped_role: str | None,
    sso_tags: Iterable[str] | None = None,
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
    normalized_tags = [tag.strip() for tag in (sso_tags or []) if isinstance(tag, str) and tag.strip()]
    capabilities = resolve_workspace_capabilities(payload, workspace_role, normalized_tags)
    sync_hash_source = "|".join([
        *(normalized_roles or []),
        *(normalized_permissions or []),
        *(normalized_tags or []),
        *(capabilities or []),
        workspace_role or "",
        mapped_role or "",
    ])

    return {
        "workspace_role": workspace_role,
        "mapped_role": mapped_role,
        "roles": normalized_roles,
        "permissions": normalized_permissions,
        "sso_tags": normalized_tags,
        "capabilities": capabilities,
        "sync_hash": hashlib.sha256(sync_hash_source.encode("utf-8")).hexdigest(),
    }


def _desktop_sso_projection_key(account_id: str, tenant_id: str) -> str:
    return f"{DESKTOP_SSO_PROJECTION_KEY_PREFIX}:{tenant_id}:{account_id}"


def _desktop_sso_group_tenant_cache_key(group_name: str) -> str:
    group_hash = hashlib.sha256(group_name.strip().lower().encode("utf-8")).hexdigest()
    return f"{DESKTOP_SSO_GROUP_TENANT_CACHE_PREFIX}{group_hash}"


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
    capabilities.update(get_admin_override_capabilities(get_account_sso_tags(account, resolved_tenant_id)))
    return sorted(capabilities)


def get_account_sso_tags(account: Any, tenant_id: str | None = None) -> list[str]:
    account_id = getattr(account, "id", None)
    resolved_tenant_id = tenant_id or getattr(account, "current_tenant_id", None)

    if isinstance(account_id, str) and resolved_tenant_id:
        projection = load_desktop_sso_projection(account_id, str(resolved_tenant_id))
        if projection:
            projection_tags = projection.get("sso_tags")
            if isinstance(projection_tags, list):
                return [tag for tag in projection_tags if isinstance(tag, str) and tag]

    custom_config = getattr(account, "custom_config_dict", None)
    if isinstance(custom_config, dict):
        stored_tags = custom_config.get("desktop_sso_tags")
        if isinstance(stored_tags, list):
            return [tag for tag in stored_tags if isinstance(tag, str) and tag]

    return []


def get_account_sso_groups(account: Any) -> list[str]:
    custom_config = getattr(account, "custom_config_dict", None)
    account_id = getattr(account, "id", None)

    if (not isinstance(custom_config, dict) or not isinstance(custom_config.get("desktop_sso_groups"), list)) and isinstance(account_id, str):
        persisted_account = db.session.query(Account).filter_by(id=account_id).first()
        if persisted_account:
            custom_config = persisted_account.custom_config_dict

    if not isinstance(custom_config, dict):
        return []

    stored_groups = custom_config.get("desktop_sso_groups")
    if not isinstance(stored_groups, list):
        return []

    normalized_groups: list[str] = []
    for group in stored_groups:
        if not isinstance(group, str):
            continue
        normalized_group = group.strip()
        if normalized_group and normalized_group not in normalized_groups:
            normalized_groups.append(normalized_group)

    return normalized_groups


def get_account_allowed_workspace_tenant_ids(account: Any) -> list[str] | None:
    groups = get_account_sso_groups(account)
    if not groups:
        return None

    allowed_tenant_ids: list[str] = []
    for group_name in groups:
        cache_key = _desktop_sso_group_tenant_cache_key(group_name)
        cached_tenant_id = None
        try:
            cached_tenant_id = redis_client.get(cache_key)
        except RuntimeError:
            cached_tenant_id = None

        if isinstance(cached_tenant_id, bytes):
            cached_tenant_id = cached_tenant_id.decode("utf-8")

        tenant = None
        if isinstance(cached_tenant_id, str) and cached_tenant_id:
            tenant = db.session.query(Tenant).filter_by(id=cached_tenant_id, status=TenantStatus.NORMAL).first()
            if tenant and tenant.name != group_name:
                tenant = None

        if not tenant:
            tenant = db.session.query(Tenant).filter_by(name=group_name, status=TenantStatus.NORMAL).first()
            if tenant:
                try:
                    redis_client.set(cache_key, tenant.id)
                except RuntimeError:
                    pass

        if tenant and tenant.id not in allowed_tenant_ids:
            allowed_tenant_ids.append(tenant.id)

    account_id = getattr(account, "id", None)
    persisted_account = db.session.query(Account).filter_by(id=account_id).first() if isinstance(account_id, str) else None
    persisted_account_name = persisted_account.name.strip() if persisted_account and isinstance(persisted_account.name, str) else None
    if isinstance(account_id, str):
        personal_tenant = None
        if persisted_account_name:
            personal_workspace_name = f"{persisted_account_name}'s Workspace"
            personal_tenant = (
                db.session.query(Tenant)
                .join(TenantAccountJoin, Tenant.id == TenantAccountJoin.tenant_id)
                .filter(
                    TenantAccountJoin.account_id == account_id,
                    Tenant.name == personal_workspace_name,
                    Tenant.status == TenantStatus.NORMAL,
                )
                .order_by(TenantAccountJoin.id.asc())
                .first()
            )

        if not personal_tenant:
            personal_tenant = (
            db.session.query(Tenant)
            .join(TenantAccountJoin, Tenant.id == TenantAccountJoin.tenant_id)
            .filter(
                TenantAccountJoin.account_id == account_id,
                TenantAccountJoin.role == TenantAccountRole.OWNER,
                Tenant.status == TenantStatus.NORMAL,
            )
            .order_by(TenantAccountJoin.id.asc())
            .first()
        )
        if personal_tenant and personal_tenant.id not in allowed_tenant_ids:
            allowed_tenant_ids.append(personal_tenant.id)

    return allowed_tenant_ids


def has_any_workspace_capability(account: Any, capabilities: Iterable[str], tenant_id: str | None = None) -> bool:
    capability_set = set(get_account_workspace_capabilities(account, tenant_id))
    return any(capability in capability_set for capability in capabilities)


def has_role_capability(role: str | None, capability: str) -> bool:
    return capability in WORKSPACE_ROLE_CAPABILITIES.get(role or "", frozenset())
