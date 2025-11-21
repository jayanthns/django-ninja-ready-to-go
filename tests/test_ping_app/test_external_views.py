import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ninja.responses import Response

from apps.ping_app.v1.schemas import PingRequestSchema
from apps.ping_app.v1.views import external_views as views


@pytest.mark.asyncio
class TestExternalViews:
    async def _make_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        return mock

    async def test_ping_external_success(self):
        req = await self._make_request()
        resp = await views.ping_external(req)

        assert isinstance(resp, Response)
        data = json.loads(resp.content)
        assert data["data"]["status"] == "healthy"
        assert data["data"]["message"] == "external ping service ready"
        req.logger.info.assert_called_with("Basic external ping endpoint accessed")

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_ping_endpoint_success(self, mock_ping_service):
        req = await self._make_request()
        payload = PingRequestSchema(endpoint="http://example.com", method="GET")

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.status_code = 200
        mock_response.response_time_ms = 100.5
        mock_response.endpoint = "http://example.com"
        mock_response.method = "GET"

        mock_ping_service.ping_endpoint = AsyncMock(return_value=mock_response)
        mock_ping_service.log_ping_result = AsyncMock()

        resp = await views.ping_endpoint(req, payload)

        assert resp["data"] == mock_response
        req.logger.info.assert_any_call(
            "Successfully pinged http://example.com - Status: 200, Time: 100.50ms"
        )

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_ping_endpoint_failure(self, mock_ping_service):
        req = await self._make_request()
        payload = PingRequestSchema(endpoint="http://bad.com", method="GET")

        mock_response = MagicMock()
        mock_response.success = False
        mock_response.status_code = 500
        mock_response.error_message = "Internal Server Error"
        mock_response.endpoint = "http://bad.com"

        mock_ping_service.ping_endpoint = AsyncMock(return_value=mock_response)
        mock_ping_service.log_ping_result = AsyncMock()

        resp = await views.ping_endpoint(req, payload)

        assert resp["data"] == mock_response
        req.logger.warning.assert_called_with(
            "Failed to ping http://bad.com - Status: 500, Error: Internal Server Error"
        )

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_ping_endpoint_exception(self, mock_ping_service):
        req = await self._make_request()
        payload = PingRequestSchema(endpoint="http://crash.com", method="GET")

        mock_ping_service.ping_endpoint = AsyncMock(side_effect=Exception("Ping crash"))

        with pytest.raises(Exception) as exc:
            await views.ping_endpoint(req, payload)

        assert "Ping crash" in str(exc.value)
        req.logger.exception.assert_called_with("Error pinging endpoint http://crash.com: Ping crash")

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_get_ping_logs_success(self, mock_ping_service):
        req = await self._make_request()
        mock_logs = [{"id": 1, "endpoint": "test"}]
        mock_ping_service.get_ping_logs = AsyncMock(return_value=mock_logs)

        resp = await views.get_ping_logs(req, limit=50)

        assert resp["data"] == mock_logs
        mock_ping_service.get_ping_logs.assert_awaited_with(50)
        req.logger.info.assert_any_call("Retrieved 1 ping logs")

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_get_ping_logs_exception(self, mock_ping_service):
        req = await self._make_request()
        mock_ping_service.get_ping_logs = AsyncMock(side_effect=Exception("Logs error"))

        with pytest.raises(Exception) as exc:
            await views.get_ping_logs(req)

        assert "Logs error" in str(exc.value)
        req.logger.exception.assert_called_with("Error retrieving ping logs: Logs error")

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_get_ping_stats_success(self, mock_ping_service):
        req = await self._make_request()
        mock_stats = MagicMock()
        mock_stats.total_pings = 100
        mock_stats.last_24h_success_rate = 95.5
        mock_ping_service.get_ping_stats = AsyncMock(return_value=mock_stats)

        resp = await views.get_ping_stats(req)

        assert resp["data"] == mock_stats
        req.logger.info.assert_any_call("Retrieved ping stats - Total: 100, Success Rate: 95.50%")

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_get_ping_stats_exception(self, mock_ping_service):
        req = await self._make_request()
        mock_ping_service.get_ping_stats = AsyncMock(side_effect=Exception("Stats error"))

        with pytest.raises(Exception) as exc:
            await views.get_ping_stats(req)

        assert "Stats error" in str(exc.value)
        req.logger.exception.assert_called_with("Error retrieving ping statistics: Stats error")

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_get_external_ping_health_healthy(self, mock_ping_service):
        req = await self._make_request()
        mock_stats = MagicMock()
        mock_stats.last_24h_success_rate = 90.0
        mock_stats.last_24h_pings = 100
        mock_stats.last_24h_successful = 90
        mock_stats.total_pings = 1000
        mock_stats.successful_pings = 900
        mock_stats.failed_pings = 100
        mock_stats.average_response_time_ms = 50.0

        mock_ping_service.get_ping_stats = AsyncMock(return_value=mock_stats)

        resp = await views.get_external_ping_health(req)

        assert resp["data"]["status"] == "healthy"
        assert resp["data"]["service_name"] == "External Ping Service"
        req.logger.info.assert_any_call("External ping service health: healthy")

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_get_external_ping_health_degraded(self, mock_ping_service):
        req = await self._make_request()
        mock_stats = MagicMock()
        mock_stats.last_24h_success_rate = 75.0
        mock_ping_service.get_ping_stats = AsyncMock(return_value=mock_stats)

        resp = await views.get_external_ping_health(req)

        assert resp["data"]["status"] == "degraded"

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_get_external_ping_health_unhealthy(self, mock_ping_service):
        req = await self._make_request()
        mock_stats = MagicMock()
        mock_stats.last_24h_success_rate = 40.0
        mock_ping_service.get_ping_stats = AsyncMock(return_value=mock_stats)

        resp = await views.get_external_ping_health(req)

        assert resp["data"]["status"] == "unhealthy"

    @patch("apps.ping_app.v1.views.external_views.PingService")
    async def test_get_external_ping_health_exception(self, mock_ping_service):
        req = await self._make_request()
        mock_ping_service.get_ping_stats = AsyncMock(side_effect=Exception("Health error"))

        with pytest.raises(Exception) as exc:
            await views.get_external_ping_health(req)

        assert "Health error" in str(exc.value)
        req.logger.exception.assert_called_with("Error getting external ping service health: Health error")
