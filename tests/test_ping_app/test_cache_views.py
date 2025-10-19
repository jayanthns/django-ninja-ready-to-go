import json
import uuid
from unittest.mock import AsyncMock, call, MagicMock, patch

import pytest

from apps.ping_app.v1.schemas import RedisHealthSchema
from apps.ping_app.v1.views.cache_views import ping_cache


@pytest.mark.asyncio
class TestCacheViewsPingCache:

    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        return mock

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
    @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
    async def test_ping_cache_on_cache_reachable_success_response(
        self, mock_log_health_check, mock_cache_health_service, mock_request
    ):

        # Assign the asyncmock
        mock_cache_health_service.check_cache_health = AsyncMock()
        mock_cache_health_service.test_cache_read = AsyncMock()
        mock_cache_health_service.test_cache_write = AsyncMock()

        fake_health_check = RedisHealthSchema(
            service_name="Redis",
            service_type="redis",
            is_healthy=True,
            response_time_ms=3,
            redis_version="1",
            memory_usage="100m",
            connected_clients="1",
        )

        mock_cache_health_service.check_cache_health.return_value = fake_health_check
        mock_cache_health_service.test_cache_read.return_value = (True, None)
        mock_cache_health_service.test_cache_write.return_value = (True, None)

        response = await ping_cache(mock_request)

        response_data = json.loads(response.content)

        # Assertions
        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

        assert response_data["data"] == {
            "is_healthy": True,
            "response_time_ms": 3.0,
            "error_message": None,
            "redis_version": "1",
            "memory_usage": "100m",
            "connected_clients": 1,
            "uptime_in_seconds": None,
            "total_commands_processed": None,
            "evicted_keys": None,
            "keyspace_hits": None,
            "keyspace_misses": None,
            "role": None,
        }

        mock_log_health_check.call_args_list == [
            call(
                service_name="Redis",
                service_type="redis",
                is_healthy=True,
                response_time_ms=3,
                error_message=None,
                metadata={"redis_version": "1", "memory_usage": "100m", "connected_clients": "1"},
            )
        ]

        assert mock_request.logger.mock_calls == [
            call.info("Pinging cache service"),
            call.info("Cache ping successful - Response time: 3.00ms"),
        ]

        # assert function calls
        mock_cache_health_service.check_cache_health.assert_called_once()
        mock_cache_health_service.test_cache_read.assert_called_once()
        mock_cache_health_service.test_cache_write.assert_called_once()

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
    @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
    async def test_ping_cache_on_cache_read_error_and_error_response(
        self, mock_log_health_check, mock_cache_health_service, mock_request
    ):

        # Assign the asyncmock
        mock_cache_health_service.check_cache_health = AsyncMock()
        mock_cache_health_service.test_cache_read = AsyncMock()
        mock_cache_health_service.test_cache_write = AsyncMock()

        # Fake Healt Check

        fake_health_check = RedisHealthSchema(
            service_name="Redis",
            service_type="redis",
            is_healthy=True,
            response_time_ms=3,
            redis_version="1",
            memory_usage="100m",
            connected_clients="1",
        )

        mock_cache_health_service.check_cache_health.return_value = fake_health_check
        mock_cache_health_service.test_cache_read.return_value = (False, "Unable to read to cache")
        mock_cache_health_service.test_cache_write.return_value = (True, None)

        response = await ping_cache(mock_request)

        response_dict = json.loads(response.content)

        # Assertions
        assert "data" in response_dict
        assert "trace_id" in response_dict
        assert "error" in response_dict

        assert response_dict["data"] == {
            "is_healthy": False,
            "response_time_ms": 3.0,
            "error_message": "Read test failed: Unable to read to cache",
            "redis_version": "1",
            "memory_usage": "100m",
            "connected_clients": 1,
            "uptime_in_seconds": None,
            "total_commands_processed": None,
            "evicted_keys": None,
            "keyspace_hits": None,
            "keyspace_misses": None,
            "role": None,
        }

        mock_log_health_check.call_args_list == [
            call(
                service_name="Redis",
                service_type="redis",
                is_healthy=False,
                response_time_ms=3,
                error_message="Read test failed: Unable to read to cache",
                metadata={"redis_version": "1", "memory_usage": "100m", "connected_clients": "1"},
            )
        ]

        assert mock_request.logger.mock_calls == [
            call.info("Pinging cache service"),
            call.warning("Cache ping failed - Read test failed: Unable to read to cache"),
        ]

        # assert function calls
        mock_cache_health_service.check_cache_health.assert_called_once()
        mock_cache_health_service.test_cache_read.assert_called_once()
        mock_cache_health_service.test_cache_write.assert_called_once()

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
    @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
    async def test_ping_cache_on_cache_write_error_and_error_response(
        self, mock_log_health_check, mock_cache_health_service, mock_request
    ):

        # Assign the asyncmock
        mock_cache_health_service.check_cache_health = AsyncMock()
        mock_cache_health_service.test_cache_read = AsyncMock()
        mock_cache_health_service.test_cache_write = AsyncMock()

        # Fake Healt Check

        fake_health_check = RedisHealthSchema(
            service_name="Redis",
            service_type="redis",
            is_healthy=True,
            response_time_ms=3,
            redis_version="1",
            memory_usage="100m",
            connected_clients="1",
        )

        mock_cache_health_service.check_cache_health.return_value = fake_health_check
        mock_cache_health_service.test_cache_read.return_value = (True, None)
        mock_cache_health_service.test_cache_write.return_value = (False, "Unable to write to cache")

        response = await ping_cache(mock_request)

        response_json = json.loads(response.content)

        # Assertions
        assert "data" in response_json
        assert "trace_id" in response_json
        assert "error" in response_json

        assert response_json["data"] == {
            "is_healthy": False,
            "response_time_ms": 3.0,
            "error_message": "Write test failed: Unable to write to cache",
            "redis_version": "1",
            "memory_usage": "100m",
            "connected_clients": 1,
            "uptime_in_seconds": None,
            "total_commands_processed": None,
            "evicted_keys": None,
            "keyspace_hits": None,
            "keyspace_misses": None,
            "role": None,
        }

        mock_log_health_check.call_args_list == [
            call(
                service_name="Redis",
                service_type="redis",
                is_healthy=False,
                response_time_ms=3,
                error_message="Write test failed: Unable to write to cache",
                metadata={"redis_version": "1", "memory_usage": "100m", "connected_clients": "1"},
            )
        ]

        assert mock_request.logger.mock_calls == [
            call.info("Pinging cache service"),
            call.warning("Cache ping failed - Write test failed: Unable to write to cache"),
        ]

        # assert function calls
        mock_cache_health_service.check_cache_health.assert_called_once()
        mock_cache_health_service.test_cache_read.assert_called_once()
        mock_cache_health_service.test_cache_write.assert_called_once()

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
    @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
    async def test_ping_cache_on_cache_read_and_write_error_and_error_response(
        self, mock_log_health_check, mock_cache_health_service, mock_request
    ):

        # Assign the asyncmock
        mock_cache_health_service.check_cache_health = AsyncMock()
        mock_cache_health_service.test_cache_read = AsyncMock()
        mock_cache_health_service.test_cache_write = AsyncMock()

        # Fake Healt Check

        fake_health_check = RedisHealthSchema(
            service_name="Redis",
            service_type="redis",
            is_healthy=True,
            response_time_ms=3,
            redis_version="1",
            memory_usage="100m",
            connected_clients="1",
        )

        mock_cache_health_service.check_cache_health.return_value = fake_health_check
        mock_cache_health_service.test_cache_read.return_value = (False, "Unable to read to cache")
        mock_cache_health_service.test_cache_write.return_value = (False, "Unable to write to cache")

        response = await ping_cache(mock_request)
        response_data = json.loads(response.content)

        # Assertions
        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

        assert response_data["data"] == {
            "is_healthy": False,
            "response_time_ms": 3.0,
            "error_message": "Read test failed: Unable to read to cache Write test failed: Unable to write to cache",
            "redis_version": "1",
            "memory_usage": "100m",
            "connected_clients": 1,
            "uptime_in_seconds": None,
            "total_commands_processed": None,
            "evicted_keys": None,
            "keyspace_hits": None,
            "keyspace_misses": None,
            "role": None,
        }

        mock_log_health_check.call_args_list == [
            call(
                service_name="Redis",
                service_type="redis",
                is_healthy=False,
                response_time_ms=3,
                error_message="Read test failed: Unable to read to cache Write test failed: Unable to write to cache",
                metadata={"redis_version": "1", "memory_usage": "100m", "connected_clients": "1"},
            )
        ]

        assert mock_request.logger.mock_calls == [
            call.info("Pinging cache service"),
            call.warning(
                "Cache ping failed - Read test failed: Unable to read to cache Write test failed: Unable to write to cache"
            ),
        ]

        # assert function calls
        mock_cache_health_service.check_cache_health.assert_called_once()
        mock_cache_health_service.test_cache_read.assert_called_once()
        mock_cache_health_service.test_cache_write.assert_called_once()

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
    @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
    async def test_ping_cache_on_cache_check_health_throw_exception_error_response(
        self, mock_log_health_check, mock_cache_health_service, mock_request
    ):
        mock_cache_health_service.check_cache_health.side_effect = AsyncMock(
            side_effect=Exception("Health check failed")
        )

        response = await ping_cache(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400

        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

        assert response_data["data"] == {}
        assert response_data["error"] == {"message": "Cache ping failed", "details": "Health check failed"}

        assert mock_request.logger.mock_calls == [
            call.info("Pinging cache service"),
            call.exception("Error pinging cache service: Health check failed"),
        ]

        mock_cache_health_service.check_cache_health.assert_called_once()
        mock_log_health_check.assert_not_called()

        mock_cache_health_service.test_cache_write.assert_not_called()
        mock_cache_health_service.test_cache_read.assert_not_called()

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
    @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
    async def test_ping_cache_on_test_cache_read_throw_exception_error_response(
        self, mock_log_health_check, mock_cache_health_service, mock_request
    ):
        # Assign the asyncmock
        mock_cache_health_service.check_cache_health = AsyncMock()

        fake_health_check = RedisHealthSchema(
            service_name="Redis",
            service_type="redis",
            is_healthy=True,
            response_time_ms=3,
            redis_version="1",
            memory_usage="100m",
            connected_clients="1",
        )

        mock_cache_health_service.check_cache_health.return_value = fake_health_check

        mock_cache_health_service.test_cache_read.side_effect = AsyncMock(side_effect=Exception("Read error"))

        response = await ping_cache(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400

        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

        assert response_data["data"] == {}
        assert response_data["error"] == {"message": "Cache ping failed", "details": "Read error"}

        assert mock_request.logger.mock_calls == [
            call.info("Pinging cache service"),
            call.exception("Error pinging cache service: Read error"),
        ]

        mock_cache_health_service.check_cache_health.assert_called_once()
        mock_log_health_check.assert_not_called()

        mock_cache_health_service.test_cache_write.assert_not_called()
        mock_cache_health_service.test_cache_read.assert_called_once()

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
    @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
    async def test_ping_cache_on_test_cache_write_throw_exception_error_response(
        self, mock_log_health_check, mock_cache_health_service, mock_request
    ):
        # Assign the asyncmock
        mock_cache_health_service.check_cache_health = AsyncMock()
        mock_cache_health_service.test_cache_read = AsyncMock()

        fake_health_check = RedisHealthSchema(
            service_name="Redis",
            service_type="redis",
            is_healthy=True,
            response_time_ms=3,
            redis_version="1",
            memory_usage="100m",
            connected_clients="1",
        )

        mock_cache_health_service.check_cache_health.return_value = fake_health_check

        mock_cache_health_service.test_cache_read.return_value = (True, None)

        mock_cache_health_service.test_cache_write.side_effect = AsyncMock(
            side_effect=Exception("Write error")
        )

        response = await ping_cache(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400

        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

        assert response_data["data"] == {}
        assert response_data["error"] == {"message": "Cache ping failed", "details": "Write error"}

        assert mock_request.logger.mock_calls == [
            call.info("Pinging cache service"),
            call.exception("Error pinging cache service: Write error"),
        ]

        mock_cache_health_service.check_cache_health.assert_called_once()
        mock_log_health_check.assert_not_called()

        mock_cache_health_service.test_cache_read.assert_called_once()
        mock_cache_health_service.test_cache_write.assert_called_once()
