from types import SimpleNamespace

from tasks import beta_application_provision_task as provision_task


class _DummyLock:
    def __init__(self, should_acquire: bool = True):
        self.should_acquire = should_acquire
        self.release_called = False
        self.acquire_called_with: dict | None = None

    def acquire(self, *, blocking: bool = True):
        self.acquire_called_with = {"blocking": blocking}
        return self.should_acquire

    def release(self):
        self.release_called = True


def test_acquire_provision_lock_success(monkeypatch):
    dummy_lock = _DummyLock(should_acquire=True)
    captured: dict[str, object] = {}

    def _fake_lock(name: str, timeout: int, blocking: bool):
        captured["name"] = name
        captured["timeout"] = timeout
        captured["blocking"] = blocking
        return dummy_lock

    monkeypatch.setattr(provision_task, "dify_config", SimpleNamespace(BETA_PROVISION_LOCK_TIMEOUT=120))
    monkeypatch.setattr(provision_task, "redis_client", SimpleNamespace(lock=_fake_lock))

    acquired_lock, lock_key = provision_task._acquire_provision_lock("app-123")

    assert lock_key == "beta:provision:app-123"
    assert acquired_lock is dummy_lock
    assert captured == {"name": "beta:provision:app-123", "timeout": 120, "blocking": False}
    assert dummy_lock.acquire_called_with == {"blocking": False}


def test_acquire_provision_lock_not_acquired(monkeypatch):
    dummy_lock = _DummyLock(should_acquire=False)

    def _fake_lock(name: str, timeout: int, blocking: bool):
        return dummy_lock

    monkeypatch.setattr(provision_task, "dify_config", SimpleNamespace(BETA_PROVISION_LOCK_TIMEOUT=180))
    monkeypatch.setattr(provision_task, "redis_client", SimpleNamespace(lock=_fake_lock))

    acquired_lock, lock_key = provision_task._acquire_provision_lock("app-456")

    assert lock_key == "beta:provision:app-456"
    assert acquired_lock is None
    assert dummy_lock.acquire_called_with == {"blocking": False}


def test_release_provision_lock_calls_release():
    dummy_lock = _DummyLock(should_acquire=True)

    provision_task._release_provision_lock(dummy_lock, "beta:provision:app-789")

    assert dummy_lock.release_called is True

