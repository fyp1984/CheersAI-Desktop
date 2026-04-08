import pytest

from models.beta_application import BetaApplication
from services.beta_application_provisioning_service import (
    BETA_APPLICATION_STATUS_FAILED,
    BETA_APPLICATION_STATUS_PENDING,
    RETRY_MODE_FROM_FAILED,
    RETRY_MODE_FULL,
    STEP_NEXUS_RESOURCE_INIT,
    BetaApplicationProvisioningService,
)


def _build_application(*, status: str, provision_attempt_count: int = 0) -> BetaApplication:
    return BetaApplication(
        id="beta-app-id",
        email="tester@example.com",
        status=status,
        provision_attempt_count=provision_attempt_count,
    )


def test_retry_rejects_invalid_mode():
    service = BetaApplicationProvisioningService()
    application = _build_application(status=BETA_APPLICATION_STATUS_FAILED, provision_attempt_count=2)

    with pytest.raises(ValueError, match="Unsupported retry mode"):
        service.retry(application, mode="invalid-mode")


def test_retry_blocks_when_manual_retry_limit_reached():
    service = BetaApplicationProvisioningService()
    application = _build_application(
        status=BETA_APPLICATION_STATUS_FAILED,
        provision_attempt_count=6,  # 1 initial + 5 manual retries
    )

    with pytest.raises(ValueError, match="Manual retry limit reached"):
        service.retry(application, mode=RETRY_MODE_FROM_FAILED)


def test_retry_uses_requested_mode(monkeypatch: pytest.MonkeyPatch):
    service = BetaApplicationProvisioningService()
    application = _build_application(status=BETA_APPLICATION_STATUS_FAILED, provision_attempt_count=1)
    captured: dict[str, str] = {}

    def _fake_provision(app: BetaApplication, *, retry_mode: str):
        captured["id"] = app.id
        captured["mode"] = retry_mode
        return {"result": "ok"}

    monkeypatch.setattr(service, "provision", _fake_provision)

    result = service.retry(application, mode=RETRY_MODE_FULL)

    assert result == {"result": "ok"}
    assert captured == {"id": "beta-app-id", "mode": RETRY_MODE_FULL}


def test_reject_reason_requires_min_length():
    service = BetaApplicationProvisioningService()
    application = _build_application(status=BETA_APPLICATION_STATUS_PENDING)

    with pytest.raises(ValueError, match="at least 5 characters"):
        service.reject(application, "短")


def test_step6_included_when_resource_init_enabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "services.beta_application_provisioning_service.dify_config.BETA_ENABLE_NEXUS_RESOURCE_INIT",
        True,
    )
    service = BetaApplicationProvisioningService()
    application = _build_application(status=BETA_APPLICATION_STATUS_PENDING)

    step_keys = service._resolve_step_keys(
        application,
        original_status=BETA_APPLICATION_STATUS_PENDING,
        retry_mode=RETRY_MODE_FULL,
    )

    assert STEP_NEXUS_RESOURCE_INIT in step_keys
