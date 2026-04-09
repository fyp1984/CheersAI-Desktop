from unittest.mock import MagicMock, patch

from redis import RedisError
from redis.connection import Connection

from extensions import ext_redis
from extensions.ext_redis import redis_fallback


def test_redis_fallback_success():
    @redis_fallback(default_return=None)
    def test_func():
        return "success"

    assert test_func() == "success"


def test_redis_fallback_error():
    @redis_fallback(default_return="fallback")
    def test_func():
        raise RedisError("Redis error")

    assert test_func() == "fallback"


def test_redis_fallback_none_default():
    @redis_fallback()
    def test_func():
        raise RedisError("Redis error")

    assert test_func() is None


def test_redis_fallback_with_args():
    @redis_fallback(default_return=0)
    def test_func(x, y):
        raise RedisError("Redis error")

    assert test_func(1, 2) == 0


def test_redis_fallback_with_kwargs():
    @redis_fallback(default_return={})
    def test_func(x=None, y=None):
        raise RedisError("Redis error")

    assert test_func(x=1, y=2) == {}


def test_redis_fallback_preserves_function_metadata():
    @redis_fallback(default_return=None)
    def test_func():
        """Test function docstring"""
        pass

    assert test_func.__name__ == "test_func"
    assert test_func.__doc__ == "Test function docstring"


def test_resolve_standalone_protocol_falls_back_to_resp2_for_legacy_redis(monkeypatch):
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_HOST", "127.0.0.1")
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_PORT", 6379)
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_USERNAME", None)
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_PASSWORD", "")
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_DB", 0)

    probe_client = MagicMock()
    probe_client.info.return_value = {"redis_version": "3.0.504"}

    with patch.object(ext_redis.redis, "Redis", return_value=probe_client):
        protocol = ext_redis._resolve_standalone_protocol(Connection, {}, requested_protocol=3)

    assert protocol == 2
    probe_client.close.assert_called_once()


def test_resolve_standalone_protocol_keeps_resp3_for_supported_redis(monkeypatch):
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_HOST", "127.0.0.1")
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_PORT", 6379)
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_USERNAME", None)
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_PASSWORD", "")
    monkeypatch.setattr(ext_redis.dify_config, "REDIS_DB", 0)

    probe_client = MagicMock()
    probe_client.info.return_value = {"redis_version": "6.2.21"}

    with patch.object(ext_redis.redis, "Redis", return_value=probe_client):
        protocol = ext_redis._resolve_standalone_protocol(Connection, {}, requested_protocol=3)

    assert protocol == 3
    probe_client.close.assert_called_once()
