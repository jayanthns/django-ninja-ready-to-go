from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.ping_app.v1.schemas import RedisHealthSchema
from apps.ping_app.v1.services.cache_health_services import CacheHealthService


@pytest.mark.asyncio
class TestCacheHealthService:
    # ---------------- Test cases for the method `check_cache_health` ----------------

    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_with_use_redis_true_returns_redis_info(
        self, mock_time, mock_cache, mock_settings
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]  # Simulate 100ms response time
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.client.get_client.return_value = mock_cache
        mock_cache.client.get_connection.return_value = mock_cache
        mock_cache.info.return_value = {
            "redis_version": "6.0.9",
            "used_memory_human": "1.23M",
            "connected_clients": 10,
            "uptime_in_seconds": 3600,
            "total_commands_processed": 10000,
            "evicted_keys": 5,
            "keyspace_hits": 8000,
            "keyspace_misses": 2000,
            "role": "master",
        }
        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = "test_1000"
        result = await CacheHealthService.check_cache_health()
        assert result.is_healthy is True
        expected = RedisHealthSchema(
            is_healthy=True,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message=None,
            redis_version="6.0.9",
            memory_usage="1.23M",
            connected_clients=10,
            uptime_in_seconds=3600,
            total_commands_processed=10000,
            evicted_keys=5,
            keyspace_hits=8000,
            keyspace_misses=2000,
            role="master",
        )

        assert result.dict() == expected.dict()
        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_called_once()
        mock_cache.adelete.assert_called_once()
        mock_cache.info.assert_called_once()

    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_with_use_redis_true_with_wrapper_get_connection_returns_redis_info(
        self, mock_time, mock_cache, mock_settings
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]  # Simulate 100ms response time
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        # client_wrapper should NOT have a `.client` attribute but should
        # implement `get_connection` directly. Make `get_connection` return
        # an object with an `info()` method so the service can call it.
        inner = MagicMock()
        inner.info.return_value = {
            "redis_version": "6.0.9",
            "used_memory_human": "1.23M",
            "connected_clients": 10,
            "uptime_in_seconds": 3600,
            "total_commands_processed": 10000,
            "evicted_keys": 5,
            "keyspace_hits": 8000,
            "keyspace_misses": 2000,
            "role": "master",
        }

        class Wrapper:
            def get_connection(self, mode):
                return inner

        client_wrapper = Wrapper()
        mock_cache.client.get_client.return_value = client_wrapper
        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = "test_1000"
        result = await CacheHealthService.check_cache_health()
        assert result.is_healthy is True
        expected = RedisHealthSchema(
            is_healthy=True,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message=None,
            redis_version="6.0.9",
            memory_usage="1.23M",
            connected_clients=10,
            uptime_in_seconds=3600,
            total_commands_processed=10000,
            evicted_keys=5,
            keyspace_hits=8000,
            keyspace_misses=2000,
            role="master",
        )

        assert result.dict() == expected.dict()
        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_called_once()
        mock_cache.adelete.assert_called_once()
        inner.info.assert_called_once()

    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_with_use_redis_true_with_wrapper_no_get_connection_returns_redis_info(
        self, mock_time, mock_cache, mock_settings
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()

        # Create a wrapper that has no `.client` and no `get_connection`,
        # but does expose `info()` so that it will be returned directly
        # by `_get_redis_client()` and used by the health check.
        class PlainWrapper:
            def info(self):
                return {
                    "redis_version": "6.2.1",
                    "used_memory_human": "512K",
                    "connected_clients": 3,
                    "uptime_in_seconds": 12345,
                    "total_commands_processed": 5000,
                    "evicted_keys": 1,
                    "keyspace_hits": 4500,
                    "keyspace_misses": 500,
                    "role": "master",
                }

        client_wrapper = PlainWrapper()
        mock_cache.client.get_client.return_value = client_wrapper

        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = "test_1000"

        result = await CacheHealthService.check_cache_health()

        assert result.is_healthy is True
        assert result.redis_version == "6.2.1"
        assert result.memory_usage == "512K"
        assert result.connected_clients == 3
        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_called_once()
        mock_cache.adelete.assert_called_once()

    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_with_use_redis_true_with_wrapper_get_connection_with_exception_returns_redis_info(
        self, mock_time, mock_cache, mock_settings
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()

        # Simulate a client_wrapper where `.client.get_connection` exists
        # but calling it raises an exception. _get_redis_client should
        # catch this and return None, so no redis info is added.
        inner = MagicMock()
        inner.get_connection.side_effect = Exception("get_connection failed")

        client_wrapper = MagicMock()
        client_wrapper.client = inner

        mock_cache.client.get_client.return_value = client_wrapper
        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = "test_1000"

        result = await CacheHealthService.check_cache_health()

        # Since obtaining the redis connection failed, the service should
        # still consider the cache write/read successful (no error) but
        # should not populate redis-specific fields.
        expected = RedisHealthSchema(
            is_healthy=True,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message=None,
            redis_version=None,
            memory_usage=None,
            connected_clients=None,
            uptime_in_seconds=None,
            total_commands_processed=None,
            evicted_keys=None,
            keyspace_hits=None,
            keyspace_misses=None,
            role=None,
        )

        assert result.dict() == expected.dict()
        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_called_once()
        mock_cache.adelete.assert_called_once()
        mock_cache.client.get_client.assert_called_once()

    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_with_use_redis_false_returns_redis_info(
        self, mock_time, mock_cache, mock_settings
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]  # Simulate 100ms response time
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.client.get_client.return_value = mock_cache
        mock_cache.client.get_connection.return_value = mock_cache
        mock_cache.info.return_value = {
            "redis_version": "6.0.9",
            "used_memory_human": "1.23M",
            "connected_clients": 10,
            "uptime_in_seconds": 3600,
            "total_commands_processed": 10000,
            "evicted_keys": 5,
            "keyspace_hits": 8000,
            "keyspace_misses": 2000,
            "role": "master",
        }
        mock_settings.USE_REDIS = False

        mock_cache.aget.return_value = "test_1000"
        result = await CacheHealthService.check_cache_health()
        assert result.is_healthy is True
        expected = RedisHealthSchema(
            is_healthy=True,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message=None,
            redis_version=None,
            memory_usage=None,
            connected_clients=None,
            uptime_in_seconds=None,
            total_commands_processed=None,
            evicted_keys=None,
            keyspace_hits=None,
            keyspace_misses=None,
            role=None,
        )

        assert result.dict() == expected.dict()

    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_value_mismatch_sets_error(
        self, mock_time, mock_cache, mock_settings
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_settings.USE_REDIS = True

        # Simulate a read that doesn't match the written value
        mock_cache.aget.return_value = "different_value"

        result = await CacheHealthService.check_cache_health()

        expected = RedisHealthSchema(
            is_healthy=False,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message="Cache read/write test failed - value mismatch",
            redis_version=None,
            memory_usage=None,
            connected_clients=None,
            uptime_in_seconds=None,
            total_commands_processed=None,
            evicted_keys=None,
            keyspace_hits=None,
            keyspace_misses=None,
            role=None,
        )

        assert result.dict() == expected.dict()

        # When mismatch occurs, adelete and redis info should not be called
        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_called_once()
        mock_cache.adelete.assert_not_called()

    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_aset_raises_exception_returns_error(
        self, mock_time, mock_cache, mock_settings
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_settings.USE_REDIS = True

        mock_cache.aset.side_effect = Exception("Redis Write failed")

        result = await CacheHealthService.check_cache_health()

        expected = RedisHealthSchema(
            is_healthy=False,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message="Cache connection failed: Redis Write failed",
            redis_version=None,
            memory_usage=None,
            connected_clients=None,
            uptime_in_seconds=None,
            total_commands_processed=None,
            evicted_keys=None,
            keyspace_hits=None,
            keyspace_misses=None,
            role=None,
        )

        assert result.dict() == expected.dict()
        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_not_called()
        mock_cache.adelete.assert_not_called()

    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_aget_raises_exception_returns_error(
        self, mock_time, mock_cache, mock_settings
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_settings.USE_REDIS = True

        mock_cache.aget.side_effect = Exception("Redis Read failed")

        result = await CacheHealthService.check_cache_health()

        expected = RedisHealthSchema(
            is_healthy=False,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message="Cache connection failed: Redis Read failed",
            redis_version=None,
            memory_usage=None,
            connected_clients=None,
            uptime_in_seconds=None,
            total_commands_processed=None,
            evicted_keys=None,
            keyspace_hits=None,
            keyspace_misses=None,
            role=None,
        )

        assert result.dict() == expected.dict()

        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_called_once()
        mock_cache.adelete.assert_not_called()

    @patch(
        "apps.ping_app.v1.services.cache_health_services.CacheHealthService._get_redis_client",
        return_value=None,
    )
    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_no_redis_client_is_handled(
        self, mock_time, mock_cache, mock_settings, mock_get_client
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.info = AsyncMock()
        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = "test_1000"

        result = await CacheHealthService.check_cache_health()

        # No redis client -> info fields remain None but health check still passes
        expected = RedisHealthSchema(
            is_healthy=True,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message=None,
            redis_version=None,
            memory_usage=None,
            connected_clients=None,
            uptime_in_seconds=None,
            total_commands_processed=None,
            evicted_keys=None,
            keyspace_hits=None,
            keyspace_misses=None,
            role=None,
        )

        assert result.dict() == expected.dict()
        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_called_once()
        mock_cache.adelete.assert_called_once()

    @patch("apps.ping_app.v1.services.cache_health_services.CacheHealthService._get_redis_client")
    @patch("apps.ping_app.v1.services.cache_health_services.settings")
    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_check_cache_health_client_info_raises_exception(
        self, mock_time, mock_cache, mock_settings, mock_get_client
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1, 1000.2]
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = "test_1000"

        # Create a fake client whose info() raises
        fake_client = MagicMock()
        fake_client.info.side_effect = Exception("Info failed")
        mock_get_client.return_value = fake_client

        result = await CacheHealthService.check_cache_health()

        # Since client.info raised, the service should mark the check as failed
        expected = RedisHealthSchema(
            is_healthy=False,
            response_time_ms=round((1000.2 - 1000.0) * 1000, 2),
            error_message="Failed to retrieve Redis info: Info failed",
            redis_version=None,
            memory_usage=None,
            connected_clients=None,
            uptime_in_seconds=None,
            total_commands_processed=None,
            evicted_keys=None,
            keyspace_hits=None,
            keyspace_misses=None,
            role=None,
        )

        assert result.dict() == expected.dict()

        mock_cache.aset.assert_called_once()
        mock_cache.aget.assert_called_once()
        mock_cache.adelete.assert_called_once()
        mock_get_client.assert_called_once()
        fake_client.info.assert_called_once()

    # ---------------- Test cases for the method `check_cache_health` ends here ----------------

    # ---------------- Test cases for the method `test_cache_write` starts here ----------------

    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_test_cache_write_successful(self, mock_time, mock_cache) -> None:
        mock_time.time.return_value = 1000.0
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.aget.return_value = "test_value"

        status, error = await CacheHealthService.test_cache_write()
        assert status is True
        assert error is None

        mock_cache.aset.assert_called_once_with("write_test_1000", "test_value", timeout=60)
        mock_cache.aget.assert_called_once_with("write_test_1000")
        mock_cache.adelete.assert_called_once_with("write_test_1000")

    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_test_cache_write_error(self, mock_time, mock_cache) -> None:
        mock_time.time.return_value = 1000.0
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()

        # Simulate read value mismatch
        mock_cache.aget.return_value = "other_value"

        status, error = await CacheHealthService.test_cache_write()

        assert status is False
        assert error == "Cache write test failed - value mismatch"

        mock_cache.aset.assert_called_once_with("write_test_1000", "test_value", timeout=60)
        mock_cache.aget.assert_called_once_with("write_test_1000")
        mock_cache.adelete.assert_not_called()

    @patch("apps.ping_app.v1.services.cache_health_services.cache")
    @patch("apps.ping_app.v1.services.cache_health_services.time")
    async def test_test_cache_write_exception(self, mock_time, mock_cache) -> None:
        mock_time.time.return_value = 1000.0
        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()

        # Simulate exception on write
        mock_cache.aset.side_effect = Exception("Write failed")

        status, error = await CacheHealthService.test_cache_write()

        assert status is False
        assert "Write failed" in error

        mock_cache.aset.assert_called_once_with("write_test_1000", "test_value", timeout=60)
        mock_cache.aget.assert_not_called()
        mock_cache.adelete.assert_not_called()

    # ---------------- Test cases for the method `test_cache_write` ends here ----------------
