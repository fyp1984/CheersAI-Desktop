from libs.desktop_auth import (
    DESKTOP_ACCESS_CAPABILITY,
    collect_sso_identifiers,
    get_role_capabilities,
    has_desktop_access,
    has_role_capability,
    normalize_sso_identifier,
    resolve_workspace_role,
)


def test_normalize_sso_identifier_supports_prefixed_values():
    assert normalize_sso_identifier("CheersAI/desktop_team_admin") == "desktop_team_admin"
    assert normalize_sso_identifier(" desktop_access ") == "desktop_access"


def test_collect_sso_identifiers_keeps_roles_permissions_and_legacy_fields():
    identifiers = collect_sso_identifiers({
        "role": "desktop_team_editor",
        "roles": ["CheersAI/desktop_team_editor"],
        "permissions": ["desktop_access", "desktop_bundle_editor"],
    })

    assert identifiers == [
        "desktop_team_editor",
        "desktop_access",
        "desktop_bundle_editor",
    ]


def test_has_desktop_access_requires_desktop_access_permission():
    assert has_desktop_access({"permissions": [DESKTOP_ACCESS_CAPABILITY]}) is True
    assert has_desktop_access({"permissions": ["desktop_bundle_admin"]}) is False


def test_resolve_workspace_role_prefers_standard_role_mapping():
    resolved_identifier, workspace_role = resolve_workspace_role({
        "roles": ["CheersAI/desktop_team_admin"],
        "permissions": ["desktop_access"],
    })

    assert resolved_identifier == "desktop_team_admin"
    assert workspace_role == "admin"


def test_resolve_workspace_role_supports_dataset_operator_bundle():
    resolved_identifier, workspace_role = resolve_workspace_role({
        "permissions": ["desktop_bundle_dataset_operator", "desktop_access"],
    })

    assert resolved_identifier == "desktop_bundle_dataset_operator"
    assert workspace_role == "dataset_operator"


def test_get_role_capabilities_matches_expected_matrix():
    capabilities = get_role_capabilities("dataset_operator")

    assert "desktop_knowledge_edit" in capabilities
    assert "desktop_team_manage" not in capabilities


def test_has_role_capability_checks_workspace_role_matrix():
    assert has_role_capability("admin", "desktop_audit_view") is True
    assert has_role_capability("normal", "desktop_audit_view") is False
