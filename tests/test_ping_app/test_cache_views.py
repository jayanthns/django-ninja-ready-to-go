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


# --------- Refactored with SRP Principle ---------------
import json
import uuid
from unittest.mock import AsyncMock, call, MagicMock, patch

import pytest

from apps.ping_app.v1.schemas import RedisHealthSchema
from apps.ping_app.v1.views.cache_views import ping_cache


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
            mock.test_cache_read = AsyncMock()
            mock.test_cache_write = AsyncMock()
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

    def _assert_service_calls(self, cache_service, check_called=True, read_called=True, write_called=True):
        """Assert cache service methods were called as expected."""
        if check_called:
            cache_service.check_cache_health.assert_called_once()
        else:
            cache_service.check_cache_health.assert_not_called()

        if read_called:
            cache_service.test_cache_read.assert_called_once()
        else:
            cache_service.test_cache_read.assert_not_called()

        if write_called:
            cache_service.test_cache_write.assert_called_once()
        else:
            cache_service.test_cache_write.assert_not_called()

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
            mock_cache_service.test_cache_read.return_value = (True, None)
            mock_cache_service.test_cache_write.return_value = (True, None)

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

    class TestPartialFailures:
        """Test scenarios where some cache operations fail."""

        async def test_ping_cache_read_failure(
            self, mock_request, mock_cache_service, mock_log_health_check, healthy_redis_schema
        ):
            """Test cache ping when read operation fails."""
            # Setup
            read_error = "Unable to read to cache"
            mock_cache_service.check_cache_health.return_value = healthy_redis_schema
            mock_cache_service.test_cache_read.return_value = (False, read_error)
            mock_cache_service.test_cache_write.return_value = (True, None)

            # Execute
            response_data, _ = await TestCacheViewsPingCache()._call_ping_cache_and_parse_response(
                mock_request
            )

            # Assert
            TestCacheViewsPingCache()._assert_common_response_structure(response_data)
            TestCacheViewsPingCache()._assert_redis_data_fields(
                response_data, is_healthy=False, error_message=f"Read test failed: {read_error}"
            )
            TestCacheViewsPingCache()._assert_logging_calls(
                mock_request.logger, success=False, error_message=f"Read test failed: {read_error}"
            )

        async def test_ping_cache_write_failure(
            self, mock_request, mock_cache_service, mock_log_health_check, healthy_redis_schema
        ):
            """Test cache ping when write operation fails."""
            # Setup
            write_error = "Unable to write to cache"
            mock_cache_service.check_cache_health.return_value = healthy_redis_schema
            mock_cache_service.test_cache_read.return_value = (True, None)
            mock_cache_service.test_cache_write.return_value = (False, write_error)

            # Execute
            response_data, _ = await TestCacheViewsPingCache()._call_ping_cache_and_parse_response(
                mock_request
            )

            # Assert
            TestCacheViewsPingCache()._assert_common_response_structure(response_data)
            TestCacheViewsPingCache()._assert_redis_data_fields(
                response_data, is_healthy=False, error_message=f"Write test failed: {write_error}"
            )
            TestCacheViewsPingCache()._assert_logging_calls(
                mock_request.logger, success=False, error_message=f"Write test failed: {write_error}"
            )

        async def test_ping_cache_read_and_write_failure(
            self, mock_request, mock_cache_service, mock_log_health_check, healthy_redis_schema
        ):
            """Test cache ping when both read and write operations fail."""
            # Setup
            read_error = "Unable to read to cache"
            write_error = "Unable to write to cache"
            mock_cache_service.check_cache_health.return_value = healthy_redis_schema
            mock_cache_service.test_cache_read.return_value = (False, read_error)
            mock_cache_service.test_cache_write.return_value = (False, write_error)

            # Execute
            response_data, _ = await TestCacheViewsPingCache()._call_ping_cache_and_parse_response(
                mock_request
            )

            # Assert
            TestCacheViewsPingCache()._assert_common_response_structure(response_data)
            expected_error = f"Read test failed: {read_error} Write test failed: {write_error}"
            TestCacheViewsPingCache()._assert_redis_data_fields(
                response_data, is_healthy=False, error_message=expected_error
            )
            TestCacheViewsPingCache()._assert_logging_calls(
                mock_request.logger, success=False, error_message=expected_error
            )

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
            TestCacheViewsPingCache()._assert_service_calls(
                mock_cache_service, check_called=True, read_called=False, write_called=False
            )
            mock_log_health_check.assert_not_called()

        async def test_ping_cache_read_exception(
            self, mock_request, mock_cache_service, mock_log_health_check, healthy_redis_schema
        ):
            """Test cache ping when read test throws an exception."""
            # Setup
            error_message = "Read error"
            mock_cache_service.check_cache_health.return_value = healthy_redis_schema
            mock_cache_service.test_cache_read.side_effect = Exception(error_message)

            # Execute
            response_data, response = await TestCacheViewsPingCache()._call_ping_cache_and_parse_response(
                mock_request
            )

            # Assert
            assert response.status_code == 400
            TestCacheViewsPingCache()._assert_common_response_structure(response_data)
            assert response_data["data"] == {}
            assert response_data["error"] == {"message": "Cache ping failed", "details": error_message}

            # Verify logging and service calls
            expected_log_calls = [
                call.info("Pinging cache service"),
                call.exception(f"Error pinging cache service: {error_message}"),
            ]
            assert mock_request.logger.mock_calls == expected_log_calls

            TestCacheViewsPingCache()._assert_service_calls(
                mock_cache_service, check_called=True, read_called=True, write_called=False
            )
            mock_log_health_check.assert_not_called()

        async def test_ping_cache_write_exception(
            self, mock_request, mock_cache_service, mock_log_health_check, healthy_redis_schema
        ):
            """Test cache ping when write test throws an exception."""
            # Setup
            error_message = "Write error"
            mock_cache_service.check_cache_health.return_value = healthy_redis_schema
            mock_cache_service.test_cache_read.return_value = (True, None)
            mock_cache_service.test_cache_write.side_effect = Exception(error_message)

            # Execute
            response_data, response = await TestCacheViewsPingCache()._call_ping_cache_and_parse_response(
                mock_request
            )

            # Assert
            assert response.status_code == 400
            TestCacheViewsPingCache()._assert_common_response_structure(response_data)
            assert response_data["data"] == {}
            assert response_data["error"] == {"message": "Cache ping failed", "details": error_message}

            # Verify logging and service calls
            expected_log_calls = [
                call.info("Pinging cache service"),
                call.exception(f"Error pinging cache service: {error_message}"),
            ]
            assert mock_request.logger.mock_calls == expected_log_calls

            TestCacheViewsPingCache()._assert_service_calls(mock_cache_service)
            mock_log_health_check.assert_not_called()
