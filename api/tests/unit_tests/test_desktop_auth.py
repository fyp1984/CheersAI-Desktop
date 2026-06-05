from unittest.mock import patch

from libs.desktop_auth import (
    DESKTOP_ACCESS_CAPABILITY,
    DESKTOP_PLUGIN_MANAGE_CAPABILITY,
    build_desktop_sso_projection,
    collect_sso_identifiers,
    get_account_workspace_capabilities,
    get_current_workspace_role,
    get_role_capabilities,
    has_any_workspace_capability,
    has_desktop_access,
    has_role_capability,
    load_desktop_sso_projection,
    normalize_sso_identifier,
    resolve_workspace_capabilities,
    resolve_workspace_role,
    save_desktop_sso_projection,
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


def test_resolve_workspace_role_prefers_higher_privilege_identifier():
    resolved_identifier, workspace_role = resolve_workspace_role({
        "role": "user",
        "roles": ["desktop_dataset_operator", "desktop_team_admin"],
        "permissions": ["desktop_access"],
    })

    assert resolved_identifier == "desktop_team_admin"
    assert workspace_role == "admin"


def test_get_role_capabilities_matches_expected_matrix():
    capabilities = get_role_capabilities("dataset_operator")

    assert "desktop_knowledge_edit" in capabilities
    assert "desktop_team_manage" not in capabilities


def test_has_role_capability_checks_workspace_role_matrix():
    assert has_role_capability("admin", "desktop_audit_view") is True
    assert has_role_capability("normal", "desktop_audit_view") is False


def test_editor_role_contains_plugin_manage_compatibility_capabilities():
    capabilities = get_role_capabilities("editor")

    assert DESKTOP_PLUGIN_MANAGE_CAPABILITY in capabilities
    assert "desktop_agent_manage" in capabilities


def test_resolve_workspace_capabilities_prefers_permissions_and_roles_union():
    capabilities = resolve_workspace_capabilities({
        "roles": ["desktop_dataset_operator"],
        "permissions": ["desktop_access", "desktop_app_view", "desktop_plugin_manage"],
    }, "dataset_operator")

    assert "desktop_access" in capabilities
    assert "desktop_app_view" in capabilities
    assert "desktop_knowledge_edit" in capabilities
    assert DESKTOP_PLUGIN_MANAGE_CAPABILITY in capabilities


def test_build_desktop_sso_projection_contains_sync_hash_and_capabilities():
    projection = build_desktop_sso_projection({
        "roles": ["desktop_team_editor"],
        "permissions": ["desktop_access", "desktop_plugin_manage"],
    }, workspace_role="editor", mapped_role="desktop_team_editor")

    assert projection["workspace_role"] == "editor"
    assert projection["mapped_role"] == "desktop_team_editor"
    assert projection["sync_hash"]
    assert DESKTOP_PLUGIN_MANAGE_CAPABILITY in projection["capabilities"]


def test_save_and_load_desktop_sso_projection_round_trip():
    stored_payload: dict[str, bytes] = {}

    with patch("libs.desktop_auth.redis_client.set") as mock_set:
        mock_set.side_effect = lambda key, value, ex=None: stored_payload.setdefault(key, value)
        save_desktop_sso_projection("account-1", "tenant-1", {"capabilities": ["desktop_access"]})

    with patch("libs.desktop_auth.redis_client.get") as mock_get:
        mock_get.side_effect = lambda key: stored_payload.get(key)
        projection = load_desktop_sso_projection("account-1", "tenant-1")

    assert projection == {"capabilities": ["desktop_access"]}


def test_get_current_workspace_role_supports_current_role_property():
    class DummyAccount:
        current_role = "admin"

    assert get_current_workspace_role(DummyAccount()) == "admin"


def test_get_account_workspace_capabilities_prefers_projection_with_role_fallback():
    class DummyAccount:
        id = "account-1"
        current_tenant_id = "tenant-1"
        current_role = "normal"

    with patch("libs.desktop_auth.load_desktop_sso_projection", return_value={"capabilities": ["desktop_knowledge_edit"]}):
        capabilities = get_account_workspace_capabilities(DummyAccount())

    assert "desktop_knowledge_edit" in capabilities
    assert "desktop_knowledge_view" in capabilities


def test_get_account_workspace_capabilities_merges_database_role_when_projection_is_stale():
    class DummyAccount:
        id = "account-1"
        current_tenant_id = "tenant-1"
        current_role = "owner"

    with patch("libs.desktop_auth.load_desktop_sso_projection", return_value={"capabilities": ["desktop_app_view"]}):
        capabilities = get_account_workspace_capabilities(DummyAccount())

    assert "desktop_app_view" in capabilities
    assert "desktop_app_edit" in capabilities


def test_has_any_workspace_capability_checks_projection_capabilities():
    class DummyAccount:
        id = "account-1"
        current_tenant_id = "tenant-1"
        current_role = "normal"

    with patch("libs.desktop_auth.load_desktop_sso_projection", return_value={"capabilities": ["desktop_plugin_manage"]}):
        assert has_any_workspace_capability(DummyAccount(), ["desktop_plugin_manage"]) is True
