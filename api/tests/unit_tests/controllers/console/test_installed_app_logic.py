from unittest.mock import Mock, patch

from controllers.console.explore.installed_app import (
    _ensure_same_tenant_installed_apps,
    _filter_accessible_installed_apps,
)


def _mock_scalars_result(items):
    result = Mock()
    result.all.return_value = items
    return result


class TestEnsureSameTenantInstalledApps:
    @patch("controllers.console.explore.installed_app.db.session")
    def test_create_missing_installed_apps_for_same_tenant(self, mock_session):
        owned_app = Mock()
        owned_app.id = "app-2"
        owned_app.tenant_id = "tenant-1"

        existing_app = Mock()
        existing_app.id = "app-1"
        existing_app.tenant_id = "tenant-1"

        existing_installed_app = Mock()
        existing_installed_app.app_id = "app-1"

        mock_session.scalars.side_effect = [
            _mock_scalars_result([existing_app, owned_app]),
            _mock_scalars_result([existing_installed_app]),
        ]

        _ensure_same_tenant_installed_apps("tenant-1")

        mock_session.add.assert_called_once()
        created_installed_app = mock_session.add.call_args.args[0]
        assert str(created_installed_app.app_id) == "app-2"
        assert created_installed_app.tenant_id == "tenant-1"
        assert created_installed_app.app_owner_tenant_id == "tenant-1"
        mock_session.commit.assert_called_once()

    @patch("controllers.console.explore.installed_app.db.session")
    def test_skip_commit_when_all_same_tenant_apps_already_materialized(self, mock_session):
        owned_app = Mock()
        owned_app.id = "app-1"
        owned_app.tenant_id = "tenant-1"

        existing_installed_app = Mock()
        existing_installed_app.app_id = "app-1"

        mock_session.scalars.side_effect = [
            _mock_scalars_result([owned_app]),
            _mock_scalars_result([existing_installed_app]),
        ]

        _ensure_same_tenant_installed_apps("tenant-1")

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


class TestFilterAccessibleInstalledApps:
    @patch("controllers.console.explore.installed_app.EnterpriseService.WebAppAuth.batch_is_user_allowed_to_access_webapps")
    @patch("controllers.console.explore.installed_app.EnterpriseService.WebAppAuth.batch_get_app_access_mode_by_id")
    def test_keep_same_tenant_apps_without_external_webapp_auth(
        self, mock_get_access_mode, mock_batch_permissions
    ):
        same_tenant_app = Mock()
        same_tenant_app.id = "app-owned"

        external_app = Mock()
        external_app.id = "app-external"

        mock_get_access_mode.return_value = {
            "app-external": Mock(access_mode="public"),
        }
        mock_batch_permissions.return_value = {
            "app-external": False,
        }

        result = _filter_accessible_installed_apps(
            [
                {"app": same_tenant_app, "app_owner_tenant_id": "tenant-1"},
                {"app": external_app, "app_owner_tenant_id": "tenant-2"},
            ],
            current_tenant_id="tenant-1",
            user_id="user-1",
        )

        assert result == [{"app": same_tenant_app, "app_owner_tenant_id": "tenant-1"}]

    @patch("controllers.console.explore.installed_app.EnterpriseService.WebAppAuth.batch_is_user_allowed_to_access_webapps")
    @patch("controllers.console.explore.installed_app.EnterpriseService.WebAppAuth.batch_get_app_access_mode_by_id")
    def test_keep_allowed_external_apps_after_permission_check(
        self, mock_get_access_mode, mock_batch_permissions
    ):
        external_app = Mock()
        external_app.id = "app-external"

        installed_app = {"app": external_app, "app_owner_tenant_id": "tenant-2"}

        mock_get_access_mode.return_value = {
            "app-external": Mock(access_mode="public"),
        }
        mock_batch_permissions.return_value = {
            "app-external": True,
        }

        result = _filter_accessible_installed_apps(
            [installed_app],
            current_tenant_id="tenant-1",
            user_id="user-1",
        )

        assert result == [installed_app]
