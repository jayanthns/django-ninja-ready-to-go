import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import your router
from apps.ping_app.v1.views.system_views import get_system_health, ping


@pytest.mark.asyncio
class TestSystemPing:
    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        return mock

    async def test_ping_endpoint_returns_pong(self, mock_request):
        """✅ Should return pong and healthy response."""
        response = await ping(mock_request)

        # 1️⃣ Check structure
        assert isinstance(response, dict)
        assert "data" in response
        assert "trace_id" in response
        assert "error" in response

        # 2️⃣ Validate content
        data = response["data"]
        assert data["message"] == "pong"
        assert data["status"] == "healthy"
        assert isinstance(response["trace_id"], str)
        assert response["error"] == {}

        # 3️⃣ Logger call check
        mock_request.logger.info.assert_called_once_with("Basic ping endpoint accessed")

    async def test_ping_trace_id_is_unique_per_call(self, mock_request):
        """✅ Each call should produce a different trace_id."""
        mock_request1 = MagicMock()
        mock_request1.logger = MagicMock()
        mock_request1.trace_id = uuid.uuid4()

        mock_request2 = MagicMock()
        mock_request2.logger = MagicMock()
        mock_request2.trace_id = uuid.uuid4()

        res1 = await ping(mock_request1)
        res2 = await ping(mock_request2)

        assert res1["trace_id"] != res2["trace_id"]


@pytest.mark.asyncio
class TestSystemHealth:

    @patch("apps.ping_app.v1.views.system_views.SystemHealthService")
    async def test_system_health_endpoint_returns_success_response(self, mock_system_health_service):
        # Step 1: Prepare fake request
        mock_request = MagicMock()
        mock_request.logger = MagicMock()
        mock_request.trace_id = str(uuid.uuid4())

        # Step 2: Setup async mocks
        mock_system_health_service.check_system_health = AsyncMock()
        mock_system_health_service.log_health_check = AsyncMock()

        # Step 3: Fake service + status
        fake_service = type(
            "FakeService",
            (),
            {
                "service_name": "redis",
                "service_type": "cache",
                "is_healthy": True,
                "response_time_ms": 10.5,
                "error_message": None,
                "metadata": {"version": "7.0"},
            },
        )()

        fake_health_status = type(
            "FakeHealthStatus",
            (),
            {
                "overall_status": "healthy",
                "services": [fake_service],
            },
        )()

        mock_system_health_service.check_system_health.return_value = fake_health_status

        # Step 4: Call the view
        response = await get_system_health(mock_request)

        # Step 5: Assertions
        assert "data" in response
        assert "trace_id" in response
        assert "error" in response

        assert response["data"].overall_status == "healthy"
        assert response["data"].services[0].service_name == "redis"
        assert response["trace_id"] == mock_request.trace_id
        assert response["error"] == {}

        mock_system_health_service.log_health_check.assert_awaited()

    @patch("apps.ping_app.v1.views.system_views.SystemHealthService")
    async def test_system_health_endpoint_returns_error_response_on_db_exception(
        self, mock_system_health_service
    ):
        # Step 1: Prepare fake request
        mock_request = MagicMock()
        mock_request.logger = MagicMock()
        mock_request.trace_id = str(uuid.uuid4())

        # Simulate async method throwing an exception
        mock_system_health_service.check_system_health = AsyncMock(
            side_effect=Exception("DB connection failed")
        )
        mock_system_health_service.log_health_check = AsyncMock()

        # --- Execute view ---
        response = await get_system_health(mock_request)

        # --- Assertions ---
        assert isinstance(response, dict)
        assert "data" in response
        assert "trace_id" in response
        assert "error" in response

        # Error structure validation
        assert response["data"] == {}
        assert "System health check failed" in response["error"]["message"]
        assert "DB connection failed" in response["error"]["details"]
        assert str(mock_request.trace_id) == response["trace_id"]

        # Log assertions
        mock_request.logger.info.assert_called_once_with("Performing system health check")
        mock_request.logger.exception.assert_called_once()

    @patch("apps.ping_app.v1.views.system_views.SystemHealthService")
    async def test_system_health_endpoint_returns_error_response_on_cache_exception(
        self, mock_system_health_service
    ):
        # Step 1: Prepare fake request
        mock_request = MagicMock()
        mock_request.logger = MagicMock()
        mock_request.trace_id = str(uuid.uuid4())

        # Simulate async method throwing an exception
        mock_system_health_service.check_system_health = AsyncMock(
            side_effect=Exception("Cache connection failed")
        )
        mock_system_health_service.log_health_check = AsyncMock()

        # --- Execute view ---
        response = await get_system_health(mock_request)

        # --- Assertions ---
        assert isinstance(response, dict)
        assert "data" in response
        assert "trace_id" in response
        assert "error" in response

        # Error structure validation
        assert response["data"] == {}
        assert "System health check failed" in response["error"]["message"]
        assert "Cache connection failed" in response["error"]["details"]
        assert str(mock_request.trace_id) == response["trace_id"]

        # Log assertions
        mock_request.logger.info.assert_called_once_with("Performing system health check")
        mock_request.logger.exception.assert_called_once()
