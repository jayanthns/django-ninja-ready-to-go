import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from django.utils import timezone

from apps.ping_app.v1.schemas import PingRequestSchema
from apps.ping_app.v1.services.ping_services import PingService


class _AsyncList:
    def __init__(self, items):
        self._items = list(items)

    def __getitem__(self, idx):
        # support slicing like objs[:limit]
        if isinstance(idx, slice):
            return _AsyncList(self._items[idx])
        return self._items[idx]

    def __aiter__(self):
        self._it = iter(self._items)
        return self

    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration


@pytest.mark.asyncio
class TestPingService:

    @patch("apps.ping_app.v1.services.ping_services.time")
    @patch("apps.ping_app.v1.services.ping_services.aiohttp.ClientSession")
    async def test_ping_endpoint_success(self, mock_client_session, mock_time) -> None:
        mock_time.time.side_effect = [1000.0, 1000.05]

        # Prepare a mock response object
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "text/plain"}

        # Mock the request context manager returned by session.request
        mock_request_cm = MagicMock()
        mock_request_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_request_cm.__aexit__ = AsyncMock(return_value=None)

        # Mock the session context manager
        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=mock_request_cm)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_client_session.return_value = mock_session

        req = PingRequestSchema(endpoint="http://example", method="GET", timeout=2, headers=None)
        res = await PingService.ping_endpoint(req)

        assert res.success is True
        assert res.status_code == 200
        assert res.error_message is None
        assert res.response_headers.get("content-type") == "text/plain"

    @patch("apps.ping_app.v1.services.ping_services.time")
    @patch("apps.ping_app.v1.services.ping_services.aiohttp.ClientSession")
    async def test_ping_endpoint_timeout(self, mock_client_session, mock_time) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1]

        # Mock session.request context where entering raises TimeoutError
        mock_request_cm = MagicMock()
        mock_request_cm.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_request_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=mock_request_cm)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_client_session.return_value = mock_session

        req = PingRequestSchema(endpoint="http://example", method="GET", timeout=1, headers=None)
        res = await PingService.ping_endpoint(req)

        assert res.success is False
        assert res.status_code == 0
        assert "timed out" in (res.error_message or "")

    @patch("apps.ping_app.v1.services.ping_services.PingLog")
    async def test_log_ping_result_creates_record(self, mock_pinglog) -> None:
        mock_ping_request = MagicMock(endpoint="http://x", method="GET", headers={})
        mock_ping_response = MagicMock(
            status_code=200, response_time_ms=10.5, success=True, error_message=None, response_headers={}
        )

        mock_record = MagicMock()
        mock_pinglog.objects.acreate = AsyncMock(return_value=mock_record)

        rec = await PingService.log_ping_result(mock_ping_request, mock_ping_response)

        mock_pinglog.objects.acreate.assert_awaited_once()
        assert rec is mock_record

    @patch("apps.ping_app.v1.services.ping_services.time")
    @patch("apps.ping_app.v1.services.ping_services.aiohttp.ClientSession")
    async def test_ping_endpoint_client_error(self, mock_client_session, mock_time) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1]

        # simulate aiohttp client error while entering request context
        mock_request_cm = MagicMock()
        mock_request_cm.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("client boom"))
        mock_request_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=mock_request_cm)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_client_session.return_value = mock_session

        req = PingRequestSchema(endpoint="http://example", method="GET", timeout=1, headers=None)
        res = await PingService.ping_endpoint(req)

        assert res.success is False
        assert res.status_code == 0
        assert "Client error" in (res.error_message or "")

    @patch("apps.ping_app.v1.services.ping_services.time")
    @patch("apps.ping_app.v1.services.ping_services.aiohttp.ClientSession")
    async def test_ping_endpoint_unexpected_exception(self, mock_client_session, mock_time) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1]

        # simulate an unexpected exception while entering request context
        mock_request_cm = MagicMock()
        mock_request_cm.__aenter__ = AsyncMock(side_effect=Exception("uh oh"))
        mock_request_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.request = MagicMock(return_value=mock_request_cm)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_client_session.return_value = mock_session

        req = PingRequestSchema(endpoint="http://example", method="GET", timeout=1, headers=None)
        res = await PingService.ping_endpoint(req)

        assert res.success is False
        assert res.status_code == 0
        assert "Unexpected error" in (res.error_message or "")

    @patch("apps.ping_app.v1.services.ping_services.PingLog")
    async def test_get_ping_logs_returns_list(self, mock_pinglog) -> None:
        # Prepare two fake PingLog objects
        p1 = MagicMock()
        p2 = MagicMock()
        mock_pinglog.objects.all.return_value = _AsyncList([p1, p2])

        logs = await PingService.get_ping_logs(limit=2)

        assert isinstance(logs, list)
        assert len(logs) == 2

    @patch("apps.ping_app.v1.services.ping_services.PingLog")
    async def test_get_ping_stats_empty(self, mock_pinglog) -> None:
        mock_pinglog.objects.all.return_value = _AsyncList([])

        stats = await PingService.get_ping_stats()

        assert stats.total_pings == 0
        assert stats.successful_pings == 0
        assert stats.failed_pings == 0

    @patch("apps.ping_app.v1.services.ping_services.PingLog")
    async def test_get_ping_stats_non_empty(self, mock_pinglog) -> None:
        now = timezone.now()
        older = now - timedelta(days=2)

        p1 = MagicMock(success=True, response_time_ms=100.0, created_at=now)
        p2 = MagicMock(success=False, response_time_ms=200.0, created_at=now)
        p3 = MagicMock(success=True, response_time_ms=50.0, created_at=older)

        mock_pinglog.objects.all.return_value = _AsyncList([p1, p2, p3])

        stats = await PingService.get_ping_stats()

        assert stats.total_pings == 3
        assert stats.successful_pings == 2
        assert stats.failed_pings == 1
        assert stats.min_response_time_ms == 50.0
        assert stats.max_response_time_ms == 200.0
        assert stats.average_response_time_ms == pytest.approx((100.0 + 200.0 + 50.0) / 3)
        assert stats.last_24h_pings == 2
        assert stats.last_24h_success_rate == pytest.approx((1 / 2) * 100)
