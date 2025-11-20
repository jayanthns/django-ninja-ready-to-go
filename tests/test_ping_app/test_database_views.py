from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.ping_app.v1.views import database_views as views


@pytest.mark.asyncio
class TestDatabaseViews:

    async def _make_request(self):
        req = MagicMock()
        req.logger = MagicMock()
        req.trace_id = "trace-123"
        req.timestamp = 123456
        return req

    @patch("apps.ping_app.v1.views.database_views.SystemHealthService")
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_ping_database_all_success(self, mock_db_svc, mock_system_health) -> None:
        req = await self._make_request()

        db_health = MagicMock()
        db_health.is_healthy = True
        db_health.response_time_ms = 12.34
        db_health.error_message = None
        db_health.connection_count = 2
        db_health.database_name = "mydb"

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)
        mock_db_svc.test_database_read = AsyncMock(return_value=(True, None))
        mock_db_svc.test_database_write = AsyncMock(return_value=(True, None))
        mock_system_health.log_health_check = AsyncMock()

        resp = await views.ping_database(req)

        assert "data" in resp
        assert resp["data"].is_healthy is True
        mock_db_svc.check_database_health.assert_awaited_once()
        mock_system_health.log_health_check.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.SystemHealthService")
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_ping_database_read_failure_marks_unhealthy(self, mock_db_svc, mock_system_health) -> None:
        req = await self._make_request()

        db_health = MagicMock()
        db_health.is_healthy = True
        db_health.response_time_ms = 10.0
        db_health.error_message = None
        db_health.connection_count = None
        db_health.database_name = None

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)
        mock_db_svc.test_database_read = AsyncMock(return_value=(False, "read failed"))
        mock_db_svc.test_database_write = AsyncMock(return_value=(True, None))
        mock_system_health.log_health_check = AsyncMock()

        resp = await views.ping_database(req)

        assert resp["data"].is_healthy is False
        assert "Read test failed" in resp["data"].error_message
        mock_system_health.log_health_check.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.SystemHealthService")
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_ping_database_write_failure_marks_unhealthy(self, mock_db_svc, mock_system_health) -> None:
        req = await self._make_request()

        db_health = MagicMock()
        db_health.is_healthy = True
        db_health.response_time_ms = 10.0
        db_health.error_message = None

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)
        mock_db_svc.test_database_read = AsyncMock(return_value=(True, None))
        mock_db_svc.test_database_write = AsyncMock(return_value=(False, "write failed"))
        mock_system_health.log_health_check = AsyncMock()

        resp = await views.ping_database(req)

        assert resp["data"].is_healthy is False
        assert "Write test failed" in resp["data"].error_message
        mock_system_health.log_health_check.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.SystemHealthService")
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_ping_database_raises_exception(self, mock_db_svc, mock_system_health) -> None:
        req = await self._make_request()

        mock_db_svc.check_database_health = AsyncMock(side_effect=Exception("boom"))

        import pytest

        with pytest.raises(Exception) as exc:
            await views.ping_database(req)

        assert "boom" in str(exc.value)
        mock_db_svc.check_database_health.assert_awaited_once()

    @patch("asgiref.sync.sync_to_async")
    async def test_database_ddl_success(self, mock_sync_to_async) -> None:
        req = await self._make_request()

        # simulate successful DDL run returning (True, None, count)
        mock_sync_to_async.return_value = AsyncMock(return_value=(True, None, 3))

        resp = await views.test_database_ddl(req)

        assert resp["data"]["success"] is True
        assert resp["data"]["record_count"] == 3

    @patch("asgiref.sync.sync_to_async")
    async def test_list_database_tables_returns_list(self, mock_sync_to_async) -> None:
        req = await self._make_request()

        mock_sync_to_async.return_value = AsyncMock(
            return_value=[("t1", "BASE TABLE", 10, 0.1), ("t2", "BASE TABLE", 0, 0.0)]
        )

        resp = await views.list_database_tables(req)

        assert resp["data"]["total_tables"] == 2
        assert len(resp["data"]["tables"]) == 2

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_get_database_info_builds_dict(self, mock_db_svc) -> None:
        req = await self._make_request()

        db_health = MagicMock()
        db_health.is_healthy = True
        db_health.response_time_ms = 5.0
        db_health.database_name = "mydb"
        db_health.connection_count = 7

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)

        resp = await views.get_database_info(req)

        assert resp["data"]["database"]["name"] == "mydb"
        assert resp["data"]["connection"]["count"] == 7

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_write_post_endpoint(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_write = AsyncMock(return_value=(True, None))

        resp = await views.test_database_write_post(req)

        assert resp["data"]["success"] is True

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_read_post_endpoint(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_read = AsyncMock(return_value=(False, "fail"))

        resp = await views.test_database_read_post(req)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "fail"

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_read_endpoint_success(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_read = AsyncMock(return_value=(True, None))

        resp = await views.test_database_read(req)

        assert resp["data"]["success"] is True
        assert resp["data"]["status"] == "healthy"
        assert resp["trace_id"] == "trace-123"
        mock_db_svc.test_database_read.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_read_endpoint_failure(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_read = AsyncMock(return_value=(False, "db read error"))

        resp = await views.test_database_read(req)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "db read error"
        assert resp["data"]["status"] == "unhealthy"
        mock_db_svc.test_database_read.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_read_endpoint_raises(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_read = AsyncMock(side_effect=Exception("boom"))

        import pytest

        with pytest.raises(Exception) as exc:
            await views.test_database_read(req)

        assert "boom" in str(exc.value)
        mock_db_svc.test_database_read.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_write_endpoint_success(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_write = AsyncMock(return_value=(True, None))

        resp = await views.test_database_write(req)

        assert resp["data"]["success"] is True
        assert resp["data"]["status"] == "healthy"
        mock_db_svc.test_database_write.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_write_endpoint_failure(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_write = AsyncMock(return_value=(False, "write error"))

        resp = await views.test_database_write(req)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "write error"
        assert resp["data"]["status"] == "unhealthy"
        mock_db_svc.test_database_write.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_write_endpoint_raises(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_write = AsyncMock(side_effect=Exception("boom write"))

        import pytest

        with pytest.raises(Exception) as exc:
            await views.test_database_write(req)

        assert "boom write" in str(exc.value)
        mock_db_svc.test_database_write.assert_awaited_once()
