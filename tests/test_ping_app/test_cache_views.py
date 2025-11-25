# --------- Refactored with SRP Principle ---------------
import json
import uuid
from unittest.mock import AsyncMock, call, MagicMock, patch

import pytest

from apps.ping_app.v1.schemas import RedisHealthSchema
from apps.ping_app.v1.views.cache_views import (
    get_cache_info,
    get_cache_keys,
    ping_cache,
    test_cache_read,
    test_cache_write,
)


@pytest.mark.asyncio
class TestCacheViewsPingCache:
    """Test suite for cache ping functionality."""

    # Constants for reusable test data
    SERVICE_NAME = "Redis"
    SERVICE_TYPE = "redis"
    REDIS_VERSION = "1"
    MEMORY_USAGE = "100m"
    CONNECTED_CLIENTS = "1"
    RESPONSE_TIME_MS = 3.0

    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        return mock

    @pytest.fixture
    def healthy_redis_schema(self):
        """Fixture for a healthy Redis health schema."""
        return RedisHealthSchema(
            service_name=self.SERVICE_NAME,
            service_type=self.SERVICE_TYPE,
            is_healthy=True,
            response_time_ms=self.RESPONSE_TIME_MS,
            redis_version=self.REDIS_VERSION,
            memory_usage=self.MEMORY_USAGE,
            connected_clients=self.CONNECTED_CLIENTS,
        )

    @pytest.fixture
    def mock_cache_service(self):
        """Fixture for mocked cache health service."""
        with patch("apps.ping_app.v1.views.cache_views.CacheHealthService") as mock:
            mock.check_cache_health = AsyncMock()
            yield mock

    @pytest.fixture
    def mock_log_health_check(self):
        """Fixture for mocked health check logging."""
        with patch(
            "apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock
        ) as mock:
            yield mock

    def _assert_common_response_structure(self, response_data):
        """Assert common response structure exists."""
        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

    def _assert_redis_data_fields(self, response_data, is_healthy=True, error_message=None):
        """Assert common Redis data fields in response."""
        expected_data = {
            "is_healthy": is_healthy,
            "response_time_ms": self.RESPONSE_TIME_MS,
            "error_message": error_message,
            "redis_version": self.REDIS_VERSION,
            "memory_usage": self.MEMORY_USAGE,
            "connected_clients": int(self.CONNECTED_CLIENTS),
            "uptime_in_seconds": None,
            "total_commands_processed": None,
            "evicted_keys": None,
            "keyspace_hits": None,
            "keyspace_misses": None,
            "role": None,
        }
        assert response_data["data"] == expected_data

    def _assert_logging_calls(self, logger_mock, success=True, error_message=None):
        """Assert appropriate logging calls were made."""
        expected_calls = [call.info("Pinging cache service")]

        if success:
            expected_calls.append(
                call.info(f"Cache ping successful - Response time: {self.RESPONSE_TIME_MS:.2f}ms")
            )
        else:
            expected_calls.append(call.warning(f"Cache ping failed - {error_message}"))

        assert logger_mock.mock_calls == expected_calls

    def _assert_service_calls(self, cache_service, check_called=True):
        """Assert cache service methods were called as expected."""
        if check_called:
            cache_service.check_cache_health.assert_called_once()
        else:
            cache_service.check_cache_health.assert_not_called()

    async def _call_ping_cache_and_parse_response(self, mock_request):
        """Helper to call ping_cache and parse JSON response."""
        response = await ping_cache(mock_request)
        return json.loads(response.content), response

    class TestSuccessfulScenarios:
        """Test successful cache ping scenarios."""

        async def test_ping_cache_successful(
            self, mock_request, mock_cache_service, mock_log_health_check, healthy_redis_schema
        ):
            """Test successful cache ping with all operations working."""
            # Setup
            mock_cache_service.check_cache_health.return_value = healthy_redis_schema

            # Execute
            response_data, _ = await TestCacheViewsPingCache()._call_ping_cache_and_parse_response(
                mock_request
            )

            # Assert
            TestCacheViewsPingCache()._assert_common_response_structure(response_data)
            TestCacheViewsPingCache()._assert_redis_data_fields(
                response_data, is_healthy=True, error_message=None
            )

            # Verify logging
            TestCacheViewsPingCache()._assert_logging_calls(mock_request.logger, success=True)

            # Verify service calls
            TestCacheViewsPingCache()._assert_service_calls(mock_cache_service)

        async def test_ping_cache_unhealthy(
            self, mock_request, mock_cache_service, mock_log_health_check, healthy_redis_schema
        ):
            """Test cache ping when health check returns unhealthy."""
            # Setup
            unhealthy_schema = healthy_redis_schema
            unhealthy_schema.is_healthy = False
            unhealthy_schema.error_message = "Cache connection failed"
            mock_cache_service.check_cache_health.return_value = unhealthy_schema

            # Execute
            response_data, _ = await TestCacheViewsPingCache()._call_ping_cache_and_parse_response(
                mock_request
            )

            # Assert
            TestCacheViewsPingCache()._assert_common_response_structure(response_data)
            TestCacheViewsPingCache()._assert_redis_data_fields(
                response_data, is_healthy=False, error_message="Cache connection failed"
            )

            # Verify logging
            TestCacheViewsPingCache()._assert_logging_calls(
                mock_request.logger, success=False, error_message="Cache connection failed"
            )

            # Verify service calls
            TestCacheViewsPingCache()._assert_service_calls(mock_cache_service)

    class TestExceptionScenarios:
        """Test scenarios where exceptions are raised."""

        async def test_ping_cache_health_check_exception(
            self, mock_request, mock_cache_service, mock_log_health_check
        ):
            """Test cache ping when health check throws an exception."""
            # Setup
            error_message = "Health check failed"
            mock_cache_service.check_cache_health.side_effect = Exception(error_message)

            # Execute
            response_data, response = await TestCacheViewsPingCache()._call_ping_cache_and_parse_response(
                mock_request
            )

            # Assert
            assert response.status_code == 400
            TestCacheViewsPingCache()._assert_common_response_structure(response_data)
            assert response_data["data"] == {}
            assert response_data["error"] == {"message": "Cache ping failed", "details": error_message}

            # Verify logging
            expected_calls = [
                call.info("Pinging cache service"),
                call.exception(f"Error pinging cache service: {error_message}"),
            ]
            assert mock_request.logger.mock_calls == expected_calls

            # Verify service calls
            TestCacheViewsPingCache()._assert_service_calls(mock_cache_service, check_called=True)
            mock_log_health_check.assert_not_called()


@pytest.mark.asyncio
class TestCacheViewsGetCacheInfo:
    """Test suite for get_cache_info functionality."""

    # Constants for reusable test data
    SERVICE_NAME = "Redis"
    SERVICE_TYPE = "redis"
    REDIS_VERSION = "1"
    MEMORY_USAGE = "100m"
    CONNECTED_CLIENTS = "1"
    RESPONSE_TIME_MS = 3.0

    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        return mock

    @pytest.fixture
    def healthy_redis_schema(self):
        """Fixture for a healthy Redis health schema."""
        return RedisHealthSchema(
            service_name=self.SERVICE_NAME,
            service_type=self.SERVICE_TYPE,
            is_healthy=True,
            response_time_ms=self.RESPONSE_TIME_MS,
            redis_version=self.REDIS_VERSION,
            memory_usage=self.MEMORY_USAGE,
            connected_clients=self.CONNECTED_CLIENTS,
        )

    @pytest.fixture
    def unhealthy_redis_schema(self):
        """Fixture for an unhealthy Redis health schema."""
        return RedisHealthSchema(
            service_name=self.SERVICE_NAME,
            service_type=self.SERVICE_TYPE,
            is_healthy=False,
            response_time_ms=self.RESPONSE_TIME_MS,
            redis_version=self.REDIS_VERSION,
            memory_usage=self.MEMORY_USAGE,
            connected_clients=self.CONNECTED_CLIENTS,
        )

    @pytest.fixture
    def mock_cache_service(self):
        """Fixture for mocked cache health service."""
        with patch("apps.ping_app.v1.views.cache_views.CacheHealthService") as mock:
            mock.check_cache_health = AsyncMock()
            yield mock

    def _assert_basic_response_structure(self, response_data):
        """Assert common response structure exists."""
        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

    def _assert_successful_response_data(self, response_data, trace_id):
        """Assert response data for successful cache info retrieval."""
        expected_data = {
            "cache_type": "Redis",
            "is_healthy": True,
            "response_time_ms": self.RESPONSE_TIME_MS,
            "server": {
                "version": self.REDIS_VERSION,
                "memory_usage": self.MEMORY_USAGE,
                "connected_clients": int(self.CONNECTED_CLIENTS),
            },
            "status": "healthy",
        }
        assert response_data["data"] == expected_data
        assert response_data["trace_id"] == trace_id
        assert response_data["error"] == {}

    def _assert_error_response_data(self, response_data, trace_id, error_details):
        """Assert response data for error scenarios."""
        assert response_data["data"] == {}
        assert response_data["trace_id"] == trace_id
        assert response_data["error"] == {
            "message": "Failed to get cache info",
            "details": error_details,
        }

    def _assert_logging_calls(self, logger_mock, success=True, error_details=None):
        """Assert appropriate logging calls were made."""
        expected_calls = [call.info("Getting cache service information")]

        if success:
            expected_calls.append(call.info("Cache info retrieved successfully"))
        else:
            expected_calls.append(call.exception(f"Failed to get cache info: {error_details}"))

        assert logger_mock.mock_calls == expected_calls

    async def _call_get_cache_info_and_parse_response(self, mock_request):
        """Helper to call get_cache_info and parse JSON response."""
        response = await get_cache_info(mock_request)
        return json.loads(response.content), response

    class TestSuccessfulScenarios:
        """Test successful cache info retrieval scenarios."""

        async def test_get_cache_info_success_response(
            self, mock_request, mock_cache_service, healthy_redis_schema
        ):
            """Test successful cache info retrieval when cache is healthy."""
            # Setup
            mock_cache_service.check_cache_health.return_value = healthy_redis_schema

            # Execute
            response_data, response = (
                await TestCacheViewsGetCacheInfo()._call_get_cache_info_and_parse_response(mock_request)
            )

            # Assert
            assert response.status_code == 200
            TestCacheViewsGetCacheInfo()._assert_basic_response_structure(response_data)
            TestCacheViewsGetCacheInfo()._assert_successful_response_data(
                response_data, str(mock_request.trace_id)
            )
            TestCacheViewsGetCacheInfo()._assert_logging_calls(mock_request.logger, success=True)
            mock_cache_service.check_cache_health.assert_called_once()

    class TestErrorScenarios:
        """Test cache info retrieval error scenarios."""

        async def test_get_cache_info_not_healthy_error_response(
            self, mock_request, mock_cache_service, unhealthy_redis_schema
        ):
            """Test cache info retrieval when cache is not healthy."""
            # Setup
            mock_cache_service.check_cache_health.return_value = unhealthy_redis_schema

            # Execute
            response_data, response = (
                await TestCacheViewsGetCacheInfo()._call_get_cache_info_and_parse_response(mock_request)
            )

            # Assert
            assert response.status_code == 400
            TestCacheViewsGetCacheInfo()._assert_basic_response_structure(response_data)
            TestCacheViewsGetCacheInfo()._assert_error_response_data(
                response_data, str(mock_request.trace_id), "Cache service is not responding"
            )
            TestCacheViewsGetCacheInfo()._assert_logging_calls(
                mock_request.logger, success=False, error_details="Cache service is not responding"
            )
            mock_cache_service.check_cache_health.assert_called_once()

        async def test_get_cache_info_cache_exception_error_response(self, mock_request, mock_cache_service):
            """Test cache info retrieval when cache service raises an exception."""
            # Setup
            error_message = "Cache unreachable exception"
            mock_cache_service.check_cache_health.side_effect = Exception(error_message)

            # Execute
            response_data, response = (
                await TestCacheViewsGetCacheInfo()._call_get_cache_info_and_parse_response(mock_request)
            )

            # Assert
            assert response.status_code == 400
            TestCacheViewsGetCacheInfo()._assert_basic_response_structure(response_data)
            TestCacheViewsGetCacheInfo()._assert_error_response_data(
                response_data, str(mock_request.trace_id), error_message
            )
            TestCacheViewsGetCacheInfo()._assert_logging_calls(
                mock_request.logger, success=False, error_details=error_message
            )
            mock_cache_service.check_cache_health.assert_called_once()


# ----------- Repeated Code more readable tests

# import json
# import uuid
# from unittest.mock import AsyncMock, call, MagicMock, patch

# import pytest

# from apps.ping_app.v1.schemas import RedisHealthSchema
# from apps.ping_app.v1.views.cache_views import ping_cache


# @pytest.mark.asyncio
# class TestCacheViewsPingCache:

#     @pytest.fixture
#     def mock_request(self):
#         """Mock a minimal Django-Ninja style request."""
#         mock = MagicMock()
#         mock.logger = MagicMock()
#         mock.trace_id = uuid.uuid4()
#         return mock

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
#     async def test_ping_cache_on_cache_reachable_success_response(
#         self, mock_log_health_check, mock_cache_health_service, mock_request
#     ):

#         # Assign the asyncmock
#         mock_cache_health_service.check_cache_health = AsyncMock()
#         mock_cache_health_service.test_cache_read = AsyncMock()
#         mock_cache_health_service.test_cache_write = AsyncMock()

#         fake_health_check = RedisHealthSchema(
#             service_name="Redis",
#             service_type="redis",
#             is_healthy=True,
#             response_time_ms=3,
#             redis_version="1",
#             memory_usage="100m",
#             connected_clients="1",
#         )

#         mock_cache_health_service.check_cache_health.return_value = fake_health_check
#         mock_cache_health_service.test_cache_read.return_value = (True, None)
#         mock_cache_health_service.test_cache_write.return_value = (True, None)

#         response = await ping_cache(mock_request)

#         response_data = json.loads(response.content)

#         # Assertions
#         assert "data" in response_data
#         assert "trace_id" in response_data
#         assert "error" in response_data

#         assert response_data["data"] == {
#             "is_healthy": True,
#             "response_time_ms": 3.0,
#             "error_message": None,
#             "redis_version": "1",
#             "memory_usage": "100m",
#             "connected_clients": 1,
#             "uptime_in_seconds": None,
#             "total_commands_processed": None,
#             "evicted_keys": None,
#             "keyspace_hits": None,
#             "keyspace_misses": None,
#             "role": None,
#         }

#         mock_log_health_check.call_args_list == [
#             call(
#                 service_name="Redis",
#                 service_type="redis",
#                 is_healthy=True,
#                 response_time_ms=3,
#                 error_message=None,
#                 metadata={"redis_version": "1", "memory_usage": "100m", "connected_clients": "1"},
#             )
#         ]

#         assert mock_request.logger.mock_calls == [
#             call.info("Pinging cache service"),
#             call.info("Cache ping successful - Response time: 3.00ms"),
#         ]

#         # assert function calls
#         mock_cache_health_service.check_cache_health.assert_called_once()
#         mock_cache_health_service.test_cache_read.assert_called_once()
#         mock_cache_health_service.test_cache_write.assert_called_once()

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
#     async def test_ping_cache_on_cache_read_error_and_error_response(
#         self, mock_log_health_check, mock_cache_health_service, mock_request
#     ):

#         # Assign the asyncmock
#         mock_cache_health_service.check_cache_health = AsyncMock()
#         mock_cache_health_service.test_cache_read = AsyncMock()
#         mock_cache_health_service.test_cache_write = AsyncMock()

#         # Fake Healt Check

#         fake_health_check = RedisHealthSchema(
#             service_name="Redis",
#             service_type="redis",
#             is_healthy=True,
#             response_time_ms=3,
#             redis_version="1",
#             memory_usage="100m",
#             connected_clients="1",
#         )

#         mock_cache_health_service.check_cache_health.return_value = fake_health_check
#         mock_cache_health_service.test_cache_read.return_value = (False, "Unable to read to cache")
#         mock_cache_health_service.test_cache_write.return_value = (True, None)

#         response = await ping_cache(mock_request)

#         response_dict = json.loads(response.content)

#         # Assertions
#         assert "data" in response_dict
#         assert "trace_id" in response_dict
#         assert "error" in response_dict

#         assert response_dict["data"] == {
#             "is_healthy": False,
#             "response_time_ms": 3.0,
#             "error_message": "Read test failed: Unable to read to cache",
#             "redis_version": "1",
#             "memory_usage": "100m",
#             "connected_clients": 1,
#             "uptime_in_seconds": None,
#             "total_commands_processed": None,
#             "evicted_keys": None,
#             "keyspace_hits": None,
#             "keyspace_misses": None,
#             "role": None,
#         }

#         mock_log_health_check.call_args_list == [
#             call(
#                 service_name="Redis",
#                 service_type="redis",
#                 is_healthy=False,
#                 response_time_ms=3,
#                 error_message="Read test failed: Unable to read to cache",
#                 metadata={"redis_version": "1", "memory_usage": "100m", "connected_clients": "1"},
#             )
#         ]

#         assert mock_request.logger.mock_calls == [
#             call.info("Pinging cache service"),
#             call.warning("Cache ping failed - Read test failed: Unable to read to cache"),
#         ]

#         # assert function calls
#         mock_cache_health_service.check_cache_health.assert_called_once()
#         mock_cache_health_service.test_cache_read.assert_called_once()
#         mock_cache_health_service.test_cache_write.assert_called_once()

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
#     async def test_ping_cache_on_cache_write_error_and_error_response(
#         self, mock_log_health_check, mock_cache_health_service, mock_request
#     ):

#         # Assign the asyncmock
#         mock_cache_health_service.check_cache_health = AsyncMock()
#         mock_cache_health_service.test_cache_read = AsyncMock()
#         mock_cache_health_service.test_cache_write = AsyncMock()

#         # Fake Healt Check

#         fake_health_check = RedisHealthSchema(
#             service_name="Redis",
#             service_type="redis",
#             is_healthy=True,
#             response_time_ms=3,
#             redis_version="1",
#             memory_usage="100m",
#             connected_clients="1",
#         )

#         mock_cache_health_service.check_cache_health.return_value = fake_health_check
#         mock_cache_health_service.test_cache_read.return_value = (True, None)
#         mock_cache_health_service.test_cache_write.return_value = (False, "Unable to write to cache")

#         response = await ping_cache(mock_request)

#         response_json = json.loads(response.content)

#         # Assertions
#         assert "data" in response_json
#         assert "trace_id" in response_json
#         assert "error" in response_json

#         assert response_json["data"] == {
#             "is_healthy": False,
#             "response_time_ms": 3.0,
#             "error_message": "Write test failed: Unable to write to cache",
#             "redis_version": "1",
#             "memory_usage": "100m",
#             "connected_clients": 1,
#             "uptime_in_seconds": None,
#             "total_commands_processed": None,
#             "evicted_keys": None,
#             "keyspace_hits": None,
#             "keyspace_misses": None,
#             "role": None,
#         }

#         mock_log_health_check.call_args_list == [
#             call(
#                 service_name="Redis",
#                 service_type="redis",
#                 is_healthy=False,
#                 response_time_ms=3,
#                 error_message="Write test failed: Unable to write to cache",
#                 metadata={"redis_version": "1", "memory_usage": "100m", "connected_clients": "1"},
#             )
#         ]

#         assert mock_request.logger.mock_calls == [
#             call.info("Pinging cache service"),
#             call.warning("Cache ping failed - Write test failed: Unable to write to cache"),
#         ]

#         # assert function calls
#         mock_cache_health_service.check_cache_health.assert_called_once()
#         mock_cache_health_service.test_cache_read.assert_called_once()
#         mock_cache_health_service.test_cache_write.assert_called_once()

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
#     async def test_ping_cache_on_cache_read_and_write_error_and_error_response(
#         self, mock_log_health_check, mock_cache_health_service, mock_request
#     ):

#         # Assign the asyncmock
#         mock_cache_health_service.check_cache_health = AsyncMock()
#         mock_cache_health_service.test_cache_read = AsyncMock()
#         mock_cache_health_service.test_cache_write = AsyncMock()

#         # Fake Healt Check

#         fake_health_check = RedisHealthSchema(
#             service_name="Redis",
#             service_type="redis",
#             is_healthy=True,
#             response_time_ms=3,
#             redis_version="1",
#             memory_usage="100m",
#             connected_clients="1",
#         )

#         mock_cache_health_service.check_cache_health.return_value = fake_health_check
#         mock_cache_health_service.test_cache_read.return_value = (False, "Unable to read to cache")
#         mock_cache_health_service.test_cache_write.return_value = (False, "Unable to write to cache")

#         response = await ping_cache(mock_request)
#         response_data = json.loads(response.content)

#         # Assertions
#         assert "data" in response_data
#         assert "trace_id" in response_data
#         assert "error" in response_data

#         assert response_data["data"] == {
#             "is_healthy": False,
#             "response_time_ms": 3.0,
#             "error_message": "Read test failed: Unable to read to cache Write test failed: Unable to write to cache",
#             "redis_version": "1",
#             "memory_usage": "100m",
#             "connected_clients": 1,
#             "uptime_in_seconds": None,
#             "total_commands_processed": None,
#             "evicted_keys": None,
#             "keyspace_hits": None,
#             "keyspace_misses": None,
#             "role": None,
#         }

#         mock_log_health_check.call_args_list == [
#             call(
#                 service_name="Redis",
#                 service_type="redis",
#                 is_healthy=False,
#                 response_time_ms=3,
#                 error_message="Read test failed: Unable to read to cache Write test failed: Unable to write to cache",
#                 metadata={"redis_version": "1", "memory_usage": "100m", "connected_clients": "1"},
#             )
#         ]

#         assert mock_request.logger.mock_calls == [
#             call.info("Pinging cache service"),
#             call.warning(
#                 "Cache ping failed - Read test failed: Unable to read to cache Write test failed: Unable to write to cache"
#             ),
#         ]

#         # assert function calls
#         mock_cache_health_service.check_cache_health.assert_called_once()
#         mock_cache_health_service.test_cache_read.assert_called_once()
#         mock_cache_health_service.test_cache_write.assert_called_once()

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
#     async def test_ping_cache_on_cache_check_health_throw_exception_error_response(
#         self, mock_log_health_check, mock_cache_health_service, mock_request
#     ):
#         mock_cache_health_service.check_cache_health.side_effect = AsyncMock(
#             side_effect=Exception("Health check failed")
#         )

#         response = await ping_cache(mock_request)

#         response_data = json.loads(response.content)

#         assert response.status_code == 400

#         assert "data" in response_data
#         assert "trace_id" in response_data
#         assert "error" in response_data

#         assert response_data["data"] == {}
#         assert response_data["error"] == {"message": "Cache ping failed", "details": "Health check failed"}

#         assert mock_request.logger.mock_calls == [
#             call.info("Pinging cache service"),
#             call.exception("Error pinging cache service: Health check failed"),
#         ]

#         mock_cache_health_service.check_cache_health.assert_called_once()
#         mock_log_health_check.assert_not_called()

#         mock_cache_health_service.test_cache_write.assert_not_called()
#         mock_cache_health_service.test_cache_read.assert_not_called()

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
#     async def test_ping_cache_on_test_cache_read_throw_exception_error_response(
#         self, mock_log_health_check, mock_cache_health_service, mock_request
#     ):
#         # Assign the asyncmock
#         mock_cache_health_service.check_cache_health = AsyncMock()

#         fake_health_check = RedisHealthSchema(
#             service_name="Redis",
#             service_type="redis",
#             is_healthy=True,
#             response_time_ms=3,
#             redis_version="1",
#             memory_usage="100m",
#             connected_clients="1",
#         )

#         mock_cache_health_service.check_cache_health.return_value = fake_health_check

#         mock_cache_health_service.test_cache_read.side_effect = AsyncMock(side_effect=Exception("Read error"))

#         response = await ping_cache(mock_request)

#         response_data = json.loads(response.content)

#         assert response.status_code == 400

#         assert "data" in response_data
#         assert "trace_id" in response_data
#         assert "error" in response_data

#         assert response_data["data"] == {}
#         assert response_data["error"] == {"message": "Cache ping failed", "details": "Read error"}

#         assert mock_request.logger.mock_calls == [
#             call.info("Pinging cache service"),
#             call.exception("Error pinging cache service: Read error"),
#         ]

#         mock_cache_health_service.check_cache_health.assert_called_once()
#         mock_log_health_check.assert_not_called()

#         mock_cache_health_service.test_cache_write.assert_not_called()
#         mock_cache_health_service.test_cache_read.assert_called_once()

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     @patch("apps.ping_app.v1.views.cache_views.SystemHealthService.log_health_check", new_callable=AsyncMock)
#     async def test_ping_cache_on_test_cache_write_throw_exception_error_response(
#         self, mock_log_health_check, mock_cache_health_service, mock_request
#     ):
#         # Assign the asyncmock
#         mock_cache_health_service.check_cache_health = AsyncMock()
#         mock_cache_health_service.test_cache_read = AsyncMock()

#         fake_health_check = RedisHealthSchema(
#             service_name="Redis",
#             service_type="redis",
#             is_healthy=True,
#             response_time_ms=3,
#             redis_version="1",
#             memory_usage="100m",
#             connected_clients="1",
#         )

#         mock_cache_health_service.check_cache_health.return_value = fake_health_check

#         mock_cache_health_service.test_cache_read.return_value = (True, None)

#         mock_cache_health_service.test_cache_write.side_effect = AsyncMock(
#             side_effect=Exception("Write error")
#         )

#         response = await ping_cache(mock_request)

#         response_data = json.loads(response.content)

#         assert response.status_code == 400

#         assert "data" in response_data
#         assert "trace_id" in response_data
#         assert "error" in response_data

#         assert response_data["data"] == {}
#         assert response_data["error"] == {"message": "Cache ping failed", "details": "Write error"}

#         assert mock_request.logger.mock_calls == [
#             call.info("Pinging cache service"),
#             call.exception("Error pinging cache service: Write error"),
#         ]

#         mock_cache_health_service.check_cache_health.assert_called_once()
#         mock_log_health_check.assert_not_called()

#         mock_cache_health_service.test_cache_read.assert_called_once()
#         mock_cache_health_service.test_cache_write.assert_called_once()

# @pytest.mark.asyncio
# class TestCacheViewsGetCacheInfo:
#     @pytest.fixture
#     def mock_request(self):
#         """Mock a minimal Django-Ninja style request."""
#         mock = MagicMock()
#         mock.logger = MagicMock()
#         mock.trace_id = uuid.uuid4()
#         return mock

#     def _assert_basic_response_data(self, response_data):
#         assert "data" in response_data
#         assert "trace_id" in response_data
#         assert "error" in response_data

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     async def test_get_cache_info_success_response(self, mock_cache_health_service, mock_request):
#         mock_cache_health_service.check_cache_health = AsyncMock()

#         fake_health_check = RedisHealthSchema(
#             service_name="Redis",
#             service_type="redis",
#             is_healthy=True,
#             response_time_ms=3,
#             redis_version="1",
#             memory_usage="100m",
#             connected_clients="1",
#         )

#         mock_cache_health_service.check_cache_health.return_value = fake_health_check

#         response = await get_cache_info(mock_request)

#         assert response.status_code == 200

#         response_data = json.loads(response.content)

#         self._assert_basic_response_data(response_data)

#         assert response_data["data"] == {
#             "cache_type": "Redis",
#             "is_healthy": True,
#             "response_time_ms": 3.0,
#             "server": {"version": "1", "memory_usage": "100m", "connected_clients": 1},
#             "status": "healthy",
#         }

#         assert response_data["trace_id"] == str(mock_request.trace_id)
#         assert response_data["error"] == {}

#         assert mock_request.logger.mock_calls == [
#             call.info("Getting cache service information"),
#             call.info("Cache info retrieved successfully"),
#         ]

#         mock_cache_health_service.check_cache_health.assert_called_once()

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     async def test_get_cache_info_not_healthy_error_response(self, mock_cache_health_service, mock_request):
#         mock_cache_health_service.check_cache_health = AsyncMock()

#         fake_health_check = RedisHealthSchema(
#             service_name="Redis",
#             service_type="redis",
#             is_healthy=False,
#             response_time_ms=3,
#             redis_version="1",
#             memory_usage="100m",
#             connected_clients="1",
#         )

#         mock_cache_health_service.check_cache_health.return_value = fake_health_check

#         response = await get_cache_info(mock_request)

#         assert response.status_code == 400

#         response_data = json.loads(response.content)

#         self._assert_basic_response_data(response_data)

#         assert response_data["data"] == {}
#         assert response_data["trace_id"] == str(mock_request.trace_id)
#         assert response_data["error"] == {
#             "message": "Failed to get cache info",
#             "details": "Cache service is not responding",
#         }

#         assert mock_request.logger.mock_calls == [
#             call.info("Getting cache service information"),
#             call.exception("Failed to get cache info: Cache service is not responding"),
#         ]

#         mock_cache_health_service.check_cache_health.assert_called_once()

#     @patch("apps.ping_app.v1.views.cache_views.CacheHealthService")
#     async def test_get_cache_info_cache_exception_error_response(
#         self, mock_cache_health_service, mock_request
#     ):
#         mock_cache_health_service.check_cache_health.side_effect = AsyncMock(
#             side_effect=Exception("Cache unreachable exception")
#         )

#         response = await get_cache_info(mock_request)

#         assert response.status_code == 400

#         response_data = json.loads(response.content)

#         self._assert_basic_response_data(response_data)

#         assert response_data["data"] == {}
#         assert response_data["trace_id"] == str(mock_request.trace_id)
#         assert response_data["error"] == {
#             "message": "Failed to get cache info",
#             "details": "Cache unreachable exception",
#         }

#         assert mock_request.logger.mock_calls == [
#             call.info("Getting cache service information"),
#             call.exception("Failed to get cache info: Cache unreachable exception"),
#         ]

#         mock_cache_health_service.check_cache_health.assert_called_once()


@pytest.mark.asyncio
class TestCacheViewsGetCacheKeys:
    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        mock.timestamp = "123456"
        return mock

    def _assert_basic_response_data(self, response_data):
        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

    @patch("django.conf.settings")
    @patch("django.core.cache.cache")
    async def test_get_cache_keys_with_default_pattern_with_request_timestamp_redis_success_response(
        self, mock_cache, mock_settings, mock_request
    ):

        mock_client = MagicMock()
        mock_connection = MagicMock()

        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.client = MagicMock()

        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = "test_123456"
        # Set up the chain: cache -> client -> get_client() -> connection
        mock_cache.client.get_client.return_value = mock_client
        mock_client.client.get_connection.return_value = mock_connection

        response = await get_cache_keys(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 200

        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {
            "cache_type": "Redis",
            "pattern": "*",
            "limit": 100,
            "keys": [],
            "status": "healthy",
        }
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {}

        assert mock_request.logger.mock_calls == [
            call.info("Getting cache keys with pattern: *, limit: 100"),
            call.info("Cache keys request completed"),
        ]

        mock_cache.aset.assert_called_once_with("cache_keys_test", "test_123456", timeout=10)
        mock_cache.aget.assert_called_once_with("cache_keys_test")
        mock_cache.adelete.assert_called_once_with("cache_keys_test")
        mock_cache.client.get_client.assert_called_once_with(write=True)
        mock_client.client.get_connection.assert_called_once_with("write")
        mock_connection.keys.assert_called_once_with("*")

    @patch("django.conf.settings")
    @patch("django.core.cache.cache")
    async def test_get_cache_keys_with_default_pattern_with_request_timestamp_redis_aget_returns_none_error_response(
        self, mock_cache, mock_settings, mock_request
    ):

        mock_client = MagicMock()
        mock_connection = MagicMock()

        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.client = MagicMock()

        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = None
        # Set up the chain: cache -> client -> get_client() -> connection
        mock_cache.client.get_client.return_value = mock_client
        mock_client.client.get_connection.return_value = mock_connection

        response = await get_cache_keys(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400

        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {}
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {
            "message": "Failed to get cache keys",
            "details": "Cache read/write test failed",
        }

        assert mock_request.logger.mock_calls == [
            call.info("Getting cache keys with pattern: *, limit: 100"),
            call.exception("Failed to get cache keys: Cache read/write test failed"),
        ]

        mock_cache.aset.assert_called_once_with("cache_keys_test", "test_123456", timeout=10)
        mock_cache.aget.assert_called_once_with("cache_keys_test")
        mock_cache.adelete.assert_not_called()
        mock_cache.client.get_client.assert_not_called()
        mock_client.client.get_connection.assert_not_called()
        mock_connection.keys.assert_not_called()

    @patch("django.conf.settings")
    @patch("django.core.cache.cache")
    async def test_get_cache_keys_with_default_pattern_with_request_timestamp_redis_aset_raise_exception_error_response(
        self, mock_cache, mock_settings, mock_request
    ):

        mock_client = MagicMock()
        mock_connection = MagicMock()

        # mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.client = MagicMock()

        mock_settings.USE_REDIS = True

        mock_cache.aset.side_effect = AsyncMock(side_effect=Exception("Redis Write failed"))
        mock_cache.aget.return_value = "test_123456"
        # Set up the chain: cache -> client -> get_client() -> connection
        mock_cache.client.get_client.return_value = mock_client
        mock_client.client.get_connection.return_value = mock_connection

        response = await get_cache_keys(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400

        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {}
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {
            "message": "Failed to get cache keys",
            "details": "Redis Write failed",
        }

        assert mock_request.logger.mock_calls == [
            call.info("Getting cache keys with pattern: *, limit: 100"),
            call.exception("Failed to get cache keys: Redis Write failed"),
        ]

        mock_cache.aset.assert_called_once_with("cache_keys_test", "test_123456", timeout=10)
        mock_cache.aget.assert_not_called()
        mock_cache.adelete.assert_not_called()
        mock_cache.client.get_client.assert_not_called()
        mock_client.client.get_connection.assert_not_called()
        mock_connection.keys.assert_not_called()

    @patch("django.conf.settings")
    @patch("django.core.cache.cache")
    async def test_get_cache_keys_with_default_pattern_with_request_timestamp_redis_aget_raise_exception_error_response(
        self, mock_cache, mock_settings, mock_request
    ):

        mock_client = MagicMock()
        mock_connection = MagicMock()

        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.client = MagicMock()

        mock_settings.USE_REDIS = True

        mock_cache.aget.side_effect = AsyncMock(side_effect=Exception("Redis Read failed"))
        # Set up the chain: cache -> client -> get_client() -> connection
        mock_cache.client.get_client.return_value = mock_client
        mock_client.client.get_connection.return_value = mock_connection

        response = await get_cache_keys(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400

        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {}
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {
            "message": "Failed to get cache keys",
            "details": "Redis Read failed",
        }

        assert mock_request.logger.mock_calls == [
            call.info("Getting cache keys with pattern: *, limit: 100"),
            call.exception("Failed to get cache keys: Redis Read failed"),
        ]

        mock_cache.aset.assert_called_once_with("cache_keys_test", "test_123456", timeout=10)
        mock_cache.aget.assert_called_once_with("cache_keys_test")
        mock_cache.adelete.assert_not_called()
        mock_cache.client.get_client.assert_not_called()
        mock_client.client.get_connection.assert_not_called()
        mock_connection.keys.assert_not_called()

    @patch("django.conf.settings")
    @patch("django.core.cache.cache")
    async def test_get_cache_keys_with_default_pattern_with_request_timestamp_redis_adelete_raise_exception_error_response(
        self, mock_cache, mock_settings, mock_request
    ):

        mock_client = MagicMock()
        mock_connection = MagicMock()

        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.client = MagicMock()

        mock_settings.USE_REDIS = True

        mock_cache.aget.return_value = "test_123456"
        mock_cache.adelete.side_effect = AsyncMock(side_effect=Exception("Redis Delete failed"))
        # Set up the chain: cache -> client -> get_client() -> connection
        mock_cache.client.get_client.return_value = mock_client
        mock_client.client.get_connection.return_value = mock_connection

        response = await get_cache_keys(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400

        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {}
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {
            "message": "Failed to get cache keys",
            "details": "Redis Delete failed",
        }

        assert mock_request.logger.mock_calls == [
            call.info("Getting cache keys with pattern: *, limit: 100"),
            call.exception("Failed to get cache keys: Redis Delete failed"),
        ]

        mock_cache.aset.assert_called_once_with("cache_keys_test", "test_123456", timeout=10)
        mock_cache.aget.assert_called_once_with("cache_keys_test")
        mock_cache.adelete.assert_called_once_with("cache_keys_test")
        mock_cache.client.get_client.assert_not_called()
        mock_client.client.get_connection.assert_not_called()
        mock_connection.keys.assert_not_called()

    @patch("django.conf.settings")
    @patch("django.core.cache.cache")
    async def test_get_cache_keys_with_default_pattern_with_request_timestamp_with_local_memory_does_not_support_key_listing(
        self, mock_cache, mock_settings, mock_request
    ):

        mock_client = MagicMock()
        mock_connection = MagicMock()

        mock_cache.aset = AsyncMock()
        mock_cache.aget = AsyncMock()
        mock_cache.adelete = AsyncMock()
        mock_cache.client = MagicMock()

        mock_settings.USE_REDIS = False

        mock_cache.aget.return_value = "test_123456"
        # Set up the chain: cache -> client -> get_client() -> connection
        mock_cache.client.get_client.return_value = mock_client
        mock_client.client.get_connection.return_value = mock_connection

        response = await get_cache_keys(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 200

        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {
            "cache_type": "LocalMemoryCache",
            "pattern": "*",
            "limit": 100,
            "message": "Local memory cache doesn't support key listing. Use Redis for key enumeration.",
            "status": "healthy",
        }
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {}

        assert mock_request.logger.mock_calls == [
            call.info("Getting cache keys with pattern: *, limit: 100"),
            call.info("Cache keys request completed"),
        ]

        mock_cache.aset.assert_called_once_with("cache_keys_test", "test_123456", timeout=10)
        mock_cache.aget.assert_called_once_with("cache_keys_test")
        mock_cache.adelete.assert_called_once_with("cache_keys_test")
        mock_cache.client.get_client.assert_not_called()
        mock_client.client.get_connection.assert_not_called()
        mock_connection.keys.assert_not_called()


@pytest.mark.asyncio
class TestCacheViewsCacheWrite:
    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        return mock

    def _assert_basic_response_data(self, response_data):
        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService.test_cache_write", new_callable=AsyncMock)
    async def test_cache_write_success_response(self, mock_test_cache_write, mock_request):

        mock_test_cache_write.return_value = (True, None)

        response = await test_cache_write(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 200
        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {
            "success": True,
            "error_message": None,
            "timestamp": str(mock_request.trace_id),
        }
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {}

        mock_test_cache_write.assert_called_once()

        assert mock_request.logger.mock_calls == [
            call.info("Testing cache write permissions"),
            call.info("Cache write test passed"),
        ]

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService.test_cache_write", new_callable=AsyncMock)
    async def test_cache_write_failed_error_response(self, mock_test_cache_write, mock_request):

        mock_test_cache_write.return_value = (False, "Cache write error")

        response = await test_cache_write(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400
        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {
            "success": False,
            "error_message": "Cache write error",
            "timestamp": str(mock_request.trace_id),
        }
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {}

        mock_test_cache_write.assert_called_once()

        assert mock_request.logger.mock_calls == [
            call.info("Testing cache write permissions"),
            call.warning("Cache write test failed - Cache write error"),
        ]

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService.test_cache_write", new_callable=AsyncMock)
    async def test_cache_write_exception_error_response(self, mock_test_cache_write, mock_request):

        mock_test_cache_write.side_effect = AsyncMock(side_effect=Exception("Cache write exception"))

        response = await test_cache_write(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400
        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {}
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {
            "message": "Error testing cache write permissions",
            "details": "Cache write exception",
        }

        mock_test_cache_write.assert_called_once()

        assert mock_request.logger.mock_calls == [
            call.info("Testing cache write permissions"),
            call.exception("Error testing cache write permissions: Cache write exception"),
        ]


@pytest.mark.asyncio
class TestCacheViewsCacheRead:
    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        return mock

    def _assert_basic_response_data(self, response_data):
        assert "data" in response_data
        assert "trace_id" in response_data
        assert "error" in response_data

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService.test_cache_read", new_callable=AsyncMock)
    async def test_cache_read_success_response(self, mock_test_cache_read, mock_request):

        mock_test_cache_read.return_value = (True, None)

        response = await test_cache_read(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 200
        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {
            "success": True,
            "error_message": None,
            "timestamp": str(mock_request.trace_id),
        }
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {}

        mock_test_cache_read.assert_called_once()

        assert mock_request.logger.mock_calls == [
            call.info("Testing cache read permissions"),
            call.info("Cache read test passed"),
        ]

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService.test_cache_read", new_callable=AsyncMock)
    async def test_cache_read_failed_error_response(self, mock_test_cache_read, mock_request):

        mock_test_cache_read.return_value = (False, "Cache read error")

        response = await test_cache_read(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400
        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {
            "success": False,
            "error_message": "Cache read error",
            "timestamp": str(mock_request.trace_id),
        }
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {}

        mock_test_cache_read.assert_called_once()

        assert mock_request.logger.mock_calls == [
            call.info("Testing cache read permissions"),
            call.warning("Cache read test failed - Cache read error"),
        ]

    @patch("apps.ping_app.v1.views.cache_views.CacheHealthService.test_cache_read", new_callable=AsyncMock)
    async def test_cache_read_exception_error_response(self, mock_test_cache_read, mock_request):

        mock_test_cache_read.side_effect = AsyncMock(side_effect=Exception("Cache read exception"))

        response = await test_cache_read(mock_request)

        response_data = json.loads(response.content)

        assert response.status_code == 400
        self._assert_basic_response_data(response_data)

        assert response_data["data"] == {}
        assert response_data["trace_id"] == str(mock_request.trace_id)
        assert response_data["error"] == {
            "message": "Error testing cache read permissions",
            "details": "Cache read exception",
        }

        mock_test_cache_read.assert_called_once()

        assert mock_request.logger.mock_calls == [
            call.info("Testing cache read permissions"),
            call.exception("Error testing cache read permissions: Cache read exception"),
        ]
