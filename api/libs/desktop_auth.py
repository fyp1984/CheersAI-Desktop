from collections.abc import Iterable, Mapping
from typing import Any

from models.account import TenantAccountRole

DESKTOP_ACCESS_CAPABILITY = "desktop_access"

WORKSPACE_ROLE_CAPABILITIES: dict[str, frozenset[str]] = {
    TenantAccountRole.OWNER: frozenset({
        "desktop_access",
        "desktop_agent_use",
        "desktop_agent_test",
        "desktop_agent_manage",
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_knowledge_edit",
        "desktop_workflow_view",
        "desktop_workflow_edit",
        "desktop_app_view",
        "desktop_app_edit",
        "desktop_explore_view",
        "desktop_settings_personal",
        "desktop_settings_team",
        "desktop_team_manage",
        "desktop_audit_view",
        "desktop_model_manage",
    }),
    TenantAccountRole.ADMIN: frozenset({
        "desktop_access",
        "desktop_agent_use",
        "desktop_agent_test",
        "desktop_agent_manage",
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_knowledge_edit",
        "desktop_workflow_view",
        "desktop_workflow_edit",
        "desktop_app_view",
        "desktop_app_edit",
        "desktop_explore_view",
        "desktop_settings_personal",
        "desktop_settings_team",
        "desktop_team_manage",
        "desktop_audit_view",
        "desktop_model_manage",
    }),
    TenantAccountRole.EDITOR: frozenset({
        "desktop_access",
        "desktop_agent_use",
        "desktop_agent_test",
        "desktop_agent_manage",
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_knowledge_edit",
        "desktop_workflow_view",
        "desktop_workflow_edit",
        "desktop_app_view",
        "desktop_app_edit",
        "desktop_explore_view",
        "desktop_settings_personal",
    }),
    TenantAccountRole.NORMAL: frozenset({
        "desktop_access",
        "desktop_agent_use",
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_explore_view",
        "desktop_settings_personal",
    }),
    TenantAccountRole.DATASET_OPERATOR: frozenset({
        "desktop_access",
        "desktop_agent_use",
        "desktop_agent_test",
        "desktop_chat_use",
        "desktop_knowledge_view",
        "desktop_knowledge_edit",
        "desktop_settings_personal",
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
    return DESKTOP_ACCESS_CAPABILITY in collect_sso_identifiers(payload)


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


def has_role_capability(role: str | None, capability: str) -> bool:
    return capability in WORKSPACE_ROLE_CAPABILITIES.get(role or "", frozenset())
