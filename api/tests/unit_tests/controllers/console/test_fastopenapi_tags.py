import builtins
import contextlib
import importlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from flask import Flask
from flask.views import MethodView

from extensions.ext_database import db


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    return app


@pytest.fixture(autouse=True)
def fix_method_view_issue(monkeypatch):
    if not hasattr(builtins, "MethodView"):
        monkeypatch.setattr(builtins, "MethodView", MethodView, raising=False)


@contextlib.contextmanager
def _patch_auth():
    def noop(func):
        return func

    default_user = MagicMock(has_edit_permission=True, is_dataset_editor=False)

    with (
        patch("controllers.console.wraps.setup_required", side_effect=noop),
        patch("libs.login.login_required", side_effect=noop),
        patch("controllers.console.wraps.account_initialization_required", side_effect=noop),
        patch("controllers.console.wraps.edit_permission_required", side_effect=noop),
        patch("libs.login.current_account_with_tenant", return_value=(default_user, "tenant-id")),
        patch("configs.dify_config.EDITION", "CLOUD"),
    ):
        yield


def _force_reload_module(target_module: str, alias_module: str):
    if target_module in sys.modules:
        del sys.modules[target_module]
    if alias_module in sys.modules:
        del sys.modules[alias_module]

    module = importlib.import_module(target_module)
    sys.modules[alias_module] = sys.modules[target_module]
    return module


def _cleanup_modules(target_module: str, alias_module: str):
    if target_module in sys.modules:
        del sys.modules[target_module]
    if alias_module in sys.modules:
        del sys.modules[alias_module]


@pytest.fixture
def tags_module():
    target_module = "controllers.console.tag.tags"
    alias_module = "api.controllers.console.tag.tags"

    try:
        with _patch_auth():
            yield _force_reload_module(target_module, alias_module)
    finally:
        _cleanup_modules(target_module, alias_module)


def test_list_tags_success(app: Flask, tags_module):
    tag = SimpleNamespace(id="tag-1", name="Alpha", type="app", binding_count=2)

    with (
        app.test_request_context("/console/api/tags?type=app&keyword=Alpha"),
        patch("controllers.console.tag.tags.TagService.get_tags", return_value=[tag]),
    ):
        response = tags_module.TagListApi().get()

    assert response == [
        {"id": "tag-1", "name": "Alpha", "type": "app", "binding_count": 2},
    ]


def test_create_tag_success(app: Flask, tags_module):
    tag = SimpleNamespace(id="tag-2", name="Beta", type="app")

    with (
        app.test_request_context("/console/api/tags", method="POST", json={"name": "Beta", "type": "app"}),
        patch("controllers.console.tag.tags._ensure_tag_manage_permission"),
        patch("controllers.console.tag.tags.TagService.save_tags", return_value=tag) as mock_save,
    ):
        response, status_code = tags_module.TagListApi().post()

    assert status_code == 201
    assert response == {
        "id": "tag-2",
        "name": "Beta",
        "type": "app",
        "binding_count": 0,
    }
    mock_save.assert_called_once_with({"name": "Beta", "type": "app"})


def test_update_tag_success(app: Flask, tags_module):
    tag = SimpleNamespace(id="tag-3", name="Gamma", type="app")

    with (
        app.test_request_context("/console/api/tags/11111111-1111-1111-1111-111111111111", method="PATCH", json={"name": "Gamma", "type": "app"}),
        patch("controllers.console.tag.tags._ensure_tag_manage_permission"),
        patch("controllers.console.tag.tags.TagService.update_tags", return_value=tag) as mock_update,
        patch("controllers.console.tag.tags.TagService.get_tag_binding_count", return_value=4),
    ):
        response = tags_module.TagApi().patch(UUID("11111111-1111-1111-1111-111111111111"))

    assert response == {
        "id": "tag-3",
        "name": "Gamma",
        "type": "app",
        "binding_count": 4,
    }
    mock_update.assert_called_once_with(
        {"name": "Gamma", "type": "app"},
        "11111111-1111-1111-1111-111111111111",
    )


def test_delete_tag_success(app: Flask, tags_module):
    tag = SimpleNamespace(id="tag-4", type="app")

    with (
        app.test_request_context("/console/api/tags/11111111-1111-1111-1111-111111111111", method="DELETE"),
        patch("controllers.console.tag.tags.TagService.get_tag", return_value=tag),
        patch("controllers.console.tag.tags._ensure_tag_manage_permission"),
        patch("controllers.console.tag.tags.TagService.delete_tag") as mock_delete,
    ):
        response, status_code = tags_module.TagApi().delete(UUID("11111111-1111-1111-1111-111111111111"))

    assert response == ""
    assert status_code == 204
    mock_delete.assert_called_once_with("11111111-1111-1111-1111-111111111111")


def test_create_tag_binding_success(app: Flask, tags_module):
    payload = {"tag_ids": ["tag-1", "tag-2"], "target_id": "target-1", "type": "app"}

    with (
        app.test_request_context("/console/api/tag-bindings/create", method="POST", json=payload),
        patch("controllers.console.tag.tags._ensure_tag_manage_permission"),
        patch("controllers.console.tag.tags.TagService.save_tag_binding") as mock_bind,
    ):
        response = tags_module.TagBindingCreateApi().post()

    assert response == {"result": "success"}
    mock_bind.assert_called_once_with(payload)


def test_delete_tag_binding_success(app: Flask, tags_module):
    payload = {"tag_id": "tag-1", "target_id": "target-1", "type": "app"}

    with (
        app.test_request_context("/console/api/tag-bindings/remove", method="POST", json=payload),
        patch("controllers.console.tag.tags._ensure_tag_manage_permission"),
        patch("controllers.console.tag.tags.TagService.delete_tag_binding") as mock_unbind,
    ):
        response = tags_module.TagBindingRemoveApi().post()

    assert response == {"result": "success"}
    mock_unbind.assert_called_once_with(payload)
