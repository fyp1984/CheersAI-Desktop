import pytest
from flask.testing import FlaskClient

import controllers.console.wraps as console_wraps
from controllers.console.auth import apply_beta
from models.beta_application import BetaApplication


def _patch_query(monkeypatch, result):
    """Replace beta application query to return a predetermined object."""

    class _Query:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return result

    monkeypatch.setattr(apply_beta.db.session, "query", lambda *args, **kwargs: _Query())


class TestApplyBetaApi:
    @pytest.fixture(autouse=True)
    def _bypass_console_auth(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(console_wraps.dify_config, "EDITION", "CLOUD")

    def test_invalid_email_returns_400(self, test_client: FlaskClient):
        payload = {"email": "not-an-email", "name": "Tester"}

        response = test_client.post("/console/api/apply-beta", json=payload)

        assert response.status_code == 400
        assert "email" in response.get_json().get("data", "").lower()

    @pytest.mark.parametrize("missing_field", ["email", "name"])
    def test_missing_required_fields(self, test_client: FlaskClient, missing_field):
        payload = {"email": "user@example.com", "name": "Valid"}
        payload.pop(missing_field)

        response = test_client.post("/console/api/apply-beta", json=payload)

        assert response.status_code in (400, 422)
        assert response.status_code != 404

    def test_duplicate_email_returns_400(self, test_client: FlaskClient, monkeypatch):
        existing_app = BetaApplication(id="existing-id", email="user@example.com", status="pending")
        _patch_query(monkeypatch, existing_app)

        payload = {"email": "user@example.com", "name": "Existing"}
        response = test_client.post("/console/api/apply-beta", json=payload)

        assert response.status_code == 400
        assert "already submitted" in response.get_json().get("data", "").lower()

    def test_success_creates_application_and_sends_notification(
        self, test_client: FlaskClient, monkeypatch
    ):
        sent = {"called": False}

        def _fake_send(*, application_id, to, name, language):
            sent["called"] = True
            sent["application_id"] = application_id

        def _empty_query(*_args, **_kwargs):
            return type("Q", (), {"filter": lambda *_: type("Self", (), {"first": lambda *_: None})()})()

        monkeypatch.setattr(apply_beta.db.session, "query", _empty_query)
        monkeypatch.setattr(apply_beta.db.session, "add", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(apply_beta.db.session, "commit", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(apply_beta.BetaApplicationNotificationService, "send_submitted_email", _fake_send)

        payload = {
            "email": "newuser@example.com",
            "name": "New User",
            "company": "CheersAI",
            "use_case": "Test",
            "language": "en-US",
        }
        response = test_client.post("/console/api/apply-beta", json=payload)

        assert response.status_code == 201
        body = response.get_json()
        assert sent["called"]
        assert body["status"] == "pending"
        assert isinstance(body["application_id"], str)
        assert len(body["application_id"]) > 10
