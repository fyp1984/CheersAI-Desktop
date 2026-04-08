from unittest.mock import patch

import pytest
from flask import Flask

from controllers.console.workspace import (
    require_knowledge_edit_capability,
    require_knowledge_view_capability,
    require_plugin_manage_capability,
    require_team_manage_capability,
    require_workflow_edit_capability,
    require_workflow_view_capability,
    require_workspace_settings_capability,
)


class TestPluginManageCapability:
    def test_should_allow_editor_role(self):
        class DummyAccount:
            current_role = "editor"

        @require_plugin_manage_capability
        def protected_view():
            return "success"

        with patch("controllers.console.wraps.current_account_with_tenant", return_value=(DummyAccount(), "tenant-1")):
            result = protected_view()

        assert result == "success"

    def test_should_reject_normal_role(self):
        app = Flask(__name__)

        class DummyAccount:
            current_role = "normal"

        @require_plugin_manage_capability
        def protected_view():
            return "success"

        with app.test_request_context():
            with patch("controllers.console.wraps.current_account_with_tenant", return_value=(DummyAccount(), "tenant-1")):
                with pytest.raises(Exception) as exc_info:
                    protected_view()

        assert exc_info.value.code == 403


class TestWorkspaceCapabilityDecorators:
    def test_should_allow_admin_to_manage_team(self):
        class DummyAccount:
            current_role = "admin"

        @require_team_manage_capability
        def protected_view():
            return "team-success"

        with patch("controllers.console.wraps.current_account_with_tenant", return_value=(DummyAccount(), "tenant-1")):
            result = protected_view()

        assert result == "team-success"

    def test_should_reject_editor_for_workspace_settings(self):
        app = Flask(__name__)

        class DummyAccount:
            current_role = "editor"

        @require_workspace_settings_capability
        def protected_view():
            return "settings-success"

        with app.test_request_context():
            with patch("controllers.console.wraps.current_account_with_tenant", return_value=(DummyAccount(), "tenant-1")):
                with pytest.raises(Exception) as exc_info:
                    protected_view()

        assert exc_info.value.code == 403

    def test_should_allow_normal_role_to_view_knowledge(self):
        class DummyAccount:
            current_role = "normal"

        @require_knowledge_view_capability
        def protected_view():
            return "knowledge-view"

        with patch("controllers.console.wraps.current_account_with_tenant", return_value=(DummyAccount(), "tenant-1")):
            result = protected_view()

        assert result == "knowledge-view"

    def test_should_reject_normal_role_to_edit_knowledge(self):
        app = Flask(__name__)

        class DummyAccount:
            current_role = "normal"

        @require_knowledge_edit_capability
        def protected_view():
            return "knowledge-edit"

        with app.test_request_context():
            with patch("controllers.console.wraps.current_account_with_tenant", return_value=(DummyAccount(), "tenant-1")):
                with pytest.raises(Exception) as exc_info:
                    protected_view()

        assert exc_info.value.code == 403

    def test_should_allow_normalized_workflow_view_capability(self):
        class DummyAccount:
            current_role = "editor"

        @require_workflow_view_capability
        def protected_view():
            return "workflow-view"

        with patch("controllers.console.wraps.current_account_with_tenant", return_value=(DummyAccount(), "tenant-1")):
            result = protected_view()

        assert result == "workflow-view"

    def test_should_reject_normal_role_to_edit_workflow(self):
        app = Flask(__name__)

        class DummyAccount:
            current_role = "normal"

        @require_workflow_edit_capability
        def protected_view():
            return "workflow-edit"

        with app.test_request_context():
            with patch("controllers.console.wraps.current_account_with_tenant", return_value=(DummyAccount(), "tenant-1")):
                with pytest.raises(Exception) as exc_info:
                    protected_view()

        assert exc_info.value.code == 403
