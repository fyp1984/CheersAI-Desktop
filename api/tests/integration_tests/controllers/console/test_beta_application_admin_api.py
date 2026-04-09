from types import SimpleNamespace

import pytest
from flask.testing import FlaskClient

import controllers.console.wraps as console_wraps
import libs.login as login_lib
from controllers.console import beta_applications
from models.account import Account, TenantAccountRole


class _FakeQuery:
    def __init__(self, items):
        self._items = items

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, limit):
        return self

    def all(self):
        return self._items


class _DummyProvisioningService:
    def __init__(self, *args, **kwargs):
        pass

    def serialize_application(self, application, include_steps=False):
        return {"id": application.id}

    def serialize_provision_task(self, task):
        return {"id": task.id, "celery_task_id": getattr(task, "celery_task_id", None)}

    def list_provision_tasks(self, application_id):
        return []

    def list_notifications(self, application_id):
        return []

    def list_steps(self, application_id):
        return []


def _patch_provisioning_service(monkeypatch):
    monkeypatch.setattr(beta_applications, "BetaApplicationProvisioningService", _DummyProvisioningService)


def _fake_query(monkeypatch, items):
    monkeypatch.setattr(beta_applications.db.session, "query", lambda *args, **kwargs: _FakeQuery(items))


def _fake_account(monkeypatch):
    fake_user = SimpleNamespace(id="user-1")
    monkeypatch.setattr(beta_applications, "current_account_with_tenant", lambda: (fake_user, "tenant-1"))


@pytest.fixture(autouse=True)
def _bypass_console_auth(monkeypatch: pytest.MonkeyPatch):
    account = Account(name="tester", email="tester@example.com")
    account.id = "acc-test-2"
    account.role = TenantAccountRole.OWNER
    account._current_tenant = SimpleNamespace(id="tenant-test-2")

    class _UserProxy:
        is_authenticated = True
        id = account.id

        def _get_current_object(self):
            return account

    monkeypatch.setattr(login_lib, "current_user", _UserProxy())
    monkeypatch.setattr(login_lib, "check_csrf_token", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(console_wraps.dify_config, "EDITION", "CLOUD")


def test_get_beta_applications_returns_items_and_total(test_client: FlaskClient, monkeypatch):
    apps = [SimpleNamespace(id="app-1"), SimpleNamespace(id="app-2")]
    _fake_query(monkeypatch, apps)
    _patch_provisioning_service(monkeypatch)

    response = test_client.get("/console/api/beta-applications")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == len(apps)
    assert len(payload["items"]) == len(apps)
    assert all(item["id"] in {"app-1", "app-2"} for item in payload["items"])


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/console/api/beta-applications/missing", None),
        ("get", "/console/api/beta-applications/missing/steps", None),
        ("get", "/console/api/beta-applications/missing/notifications", None),
        ("get", "/console/api/beta-applications/missing/provision-tasks", None),
        ("get", "/console/api/beta-applications/missing/provision-tasks/any-task", None),
        ("post", "/console/api/beta-applications/missing/provision", None),
        ("post", "/console/api/beta-applications/missing/approve", None),
        ("post", "/console/api/beta-applications/missing/retry", {"mode": "from_failed"}),
        ("post", "/console/api/beta-applications/missing/reject", {"reason": "too short"}),
    ],
)
def test_missing_application_endpoints_return_404(test_client: FlaskClient, monkeypatch, method, path, payload):
    monkeypatch.setattr(beta_applications, "_get_beta_application", lambda *_: None)
    _patch_provisioning_service(monkeypatch)
    _fake_account(monkeypatch)

    request_func = getattr(test_client, method)
    response = request_func(path, json=payload)

    assert response.status_code == 404


def test_approve_dispatches_provision_task(test_client: FlaskClient, monkeypatch):
    application = SimpleNamespace(id="app-approve", status="pending")
    monkeypatch.setattr(beta_applications, "_get_beta_application", lambda *_: application)
    _patch_provisioning_service(monkeypatch)
    _fake_account(monkeypatch)
    monkeypatch.setattr(beta_applications, "_record_operation_log", lambda **_kwargs: None)

    recorded = {}

    def fake_enqueue(*, application_id, action, mode, requested_by, requested_tenant_id):
        recorded["args"] = {
            "application_id": application_id,
            "action": action,
            "mode": mode,
            "requested_by": requested_by,
            "requested_tenant_id": requested_tenant_id,
        }
        return SimpleNamespace(id="task-1", celery_task_id="celery-1")

    monkeypatch.setattr(beta_applications, "_enqueue_provision_task", fake_enqueue)

    response = test_client.post(f"/console/api/beta-applications/{application.id}/approve")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["task"]["id"] == "task-1"
    assert recorded["args"]["action"] == beta_applications.ACTION_APPROVE
    assert recorded["args"]["application_id"] == application.id
