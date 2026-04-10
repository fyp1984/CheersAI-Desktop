from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from controllers.console.auth.desktop_sso import (
    _ensure_desktop_sso_tenant_join,
    _get_sso_group_name,
    _get_sso_group_tenant_cache_key,
)


def test_get_sso_group_name_returns_first_non_empty_group():
    payload = {
        "groups": ["", "  ", "CheersAI/系统内测", "CheersAI/其他组"],
    }

    result = _get_sso_group_name(payload)

    assert result == "CheersAI/系统内测"


def test_get_sso_group_tenant_cache_key_is_stable():
    first_key = _get_sso_group_tenant_cache_key("CheersAI/系统内测")
    second_key = _get_sso_group_tenant_cache_key(" cheersai/系统内测 ")

    assert first_key == second_key
    assert first_key.startswith("desktop:sso:group-tenant:")


@patch("controllers.console.auth.desktop_sso.TenantService.switch_tenant")
@patch("controllers.console.auth.desktop_sso.TenantService.create_tenant_member")
@patch("controllers.console.auth.desktop_sso._resolve_shared_tenant")
def test_ensure_desktop_sso_tenant_join_uses_shared_tenant_mapping(
    mock_resolve_shared_tenant, mock_create_tenant_member, mock_switch_tenant
):
    account = SimpleNamespace(id="account-1")
    tenant = SimpleNamespace(id="tenant-1")
    tenant_join = SimpleNamespace(tenant_id="tenant-1", role="admin")

    mock_resolve_shared_tenant.return_value = tenant
    mock_create_tenant_member.return_value = tenant_join

    result = _ensure_desktop_sso_tenant_join(account, "admin", {"groups": ["CheersAI/系统内测"]})

    assert result == tenant_join
    mock_create_tenant_member.assert_called_once_with(tenant, account, role="admin")
    mock_switch_tenant.assert_called_once_with(account, "tenant-1")


@patch("controllers.console.auth.desktop_sso.TenantService.switch_tenant")
@patch("controllers.console.auth.desktop_sso.db.session")
@patch("controllers.console.auth.desktop_sso._get_preferred_tenant_join")
@patch("controllers.console.auth.desktop_sso.TenantService.create_owner_tenant_if_not_exist")
@patch("controllers.console.auth.desktop_sso._resolve_shared_tenant", return_value=None)
def test_ensure_desktop_sso_tenant_join_falls_back_to_existing_membership(
    _mock_resolve_shared_tenant,
    mock_create_owner_tenant,
    mock_get_preferred_tenant_join,
    mock_session,
    mock_switch_tenant,
):
    account = SimpleNamespace(id="account-1")
    tenant_join = MagicMock()
    tenant_join.tenant_id = "tenant-2"
    tenant_join.role = "normal"
    mock_get_preferred_tenant_join.return_value = tenant_join

    result = _ensure_desktop_sso_tenant_join(account, "editor", {})

    assert result == tenant_join
    assert tenant_join.role == "editor"
    mock_create_owner_tenant.assert_called_once_with(account, is_setup=True)
    mock_session.commit.assert_called_once()
    mock_switch_tenant.assert_called_once_with(account, "tenant-2")
