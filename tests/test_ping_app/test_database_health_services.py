from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.ping_app.v1.services.database_health_services import DatabaseHealthService


@pytest.mark.asyncio
class TestDatabaseHealthService:

    @patch("apps.ping_app.v1.services.database_health_services.connection")
    @patch("apps.ping_app.v1.services.database_health_services.time")
    async def test_check_database_health_success(self, mock_time, mock_connection) -> None:
        mock_time.time.side_effect = [1000.0, 1000.1]

        # Build a cursor context manager that returns sequential fetchone results:
        # first (1,) for SELECT 1, then ('mydb',) for current_database(), then (5,) for connection count
        cursor = MagicMock()
        cursor.execute = MagicMock()
        cursor.fetchone.side_effect = [(1,), ("mydb",), (5,)]

        cm = MagicMock()
        cm.__enter__.return_value = cursor
        cm.__exit__.return_value = None

        mock_connection.cursor.return_value = cm

        result = await DatabaseHealthService.check_database_health()

        assert result.is_healthy is True
        assert result.error_message is None
        assert result.connection_count == 5
        assert result.database_name == "mydb"
        assert result.response_time_ms == pytest.approx((1000.1 - 1000.0) * 1000, rel=1e-3)
        mock_connection.cursor.assert_called_once()

    @patch("apps.ping_app.v1.services.database_health_services.connection")
    @patch("apps.ping_app.v1.services.database_health_services.time")
    async def test_check_database_health_unexpected_result(self, mock_time, mock_connection) -> None:
        mock_time.time.side_effect = [1000.0, 1000.05]

        # Simulate cursor returning a non-1 for the first SELECT 1
        cursor = MagicMock()
        cursor.execute = MagicMock()
        cursor.fetchone.return_value = (0,)

        cm = MagicMock()
        cm.__enter__.return_value = cursor
        cm.__exit__.return_value = None

        mock_connection.cursor.return_value = cm

        result = await DatabaseHealthService.check_database_health()

        assert result.is_healthy is False
        assert result.error_message == "Database query returned unexpected result"
        assert result.response_time_ms == pytest.approx((1000.05 - 1000.0) * 1000, rel=1e-3)
        mock_connection.cursor.assert_called_once()

    @patch("apps.ping_app.v1.services.database_health_services.connection")
    @patch("apps.ping_app.v1.services.database_health_services.time")
    async def test_check_database_health_sync_raises(self, mock_time, mock_connection) -> None:
        mock_time.time.side_effect = [1000.0, 1000.2]

        # Simulate connection.cursor() raising, which should propagate as a database connection failure
        mock_connection.cursor.side_effect = Exception("boom")

        result = await DatabaseHealthService.check_database_health()

        assert result.is_healthy is False
        assert "Database connection failed: boom" in result.error_message
        assert result.response_time_ms == pytest.approx((1000.2 - 1000.0) * 1000, rel=1e-3)
        mock_connection.cursor.assert_called_once()

    @patch("apps.ping_app.v1.services.database_health_services.connection")
    @patch("apps.ping_app.v1.services.database_health_services.time")
    async def test_check_database_health_count_query_raises_is_handled(
        self, mock_time, mock_connection
    ) -> None:
        mock_time.time.side_effect = [1000.0, 1000.12]

        # Simulate successful SELECT 1 and current_database(), but fail the
        # pg_stat_activity count query (should be swallowed by inner except)
        cursor = MagicMock()
        # execute called three times: SELECT 1, SELECT current_database(), SELECT count(*) ...
        cursor.execute.side_effect = [None, None, Exception("not postgres")]
        cursor.fetchone.side_effect = [(1,), ("mydb",), None]

        cm = MagicMock()
        cm.__enter__.return_value = cursor
        cm.__exit__.return_value = None

        mock_connection.cursor.return_value = cm

        result = await DatabaseHealthService.check_database_health()

        # The count query failed but was swallowed; database_name should be set,
        # connection_count remains None, and overall health is True
        assert result.is_healthy is True
        assert result.error_message is None
        assert result.database_name == "mydb"
        assert result.connection_count is None
        assert result.response_time_ms == pytest.approx((1000.12 - 1000.0) * 1000, rel=1e-3)
        mock_connection.cursor.assert_called_once()

    @patch("apps.ping_app.v1.services.database_health_services.SystemHealth")
    async def test_test_database_write_success(self, mock_system_health) -> None:
        # Mock the model manager create and returned instance
        mock_record = MagicMock()
        mock_record.adelete = AsyncMock()
        mock_system_health.objects.acreate = AsyncMock(return_value=mock_record)

        status, error = await DatabaseHealthService.test_database_write()

        assert status is True
        assert error is None
        mock_system_health.objects.acreate.assert_called_once()
        mock_record.adelete.assert_awaited_once()

    @patch("apps.ping_app.v1.services.database_health_services.SystemHealth")
    async def test_test_database_write_exception(self, mock_system_health) -> None:
        mock_system_health.objects.acreate = AsyncMock(side_effect=Exception("DB write failed"))

        status, error = await DatabaseHealthService.test_database_write()

        assert status is False
        assert "DB write failed" in error
        mock_system_health.objects.acreate.assert_called_once()

    @patch("apps.ping_app.v1.services.database_health_services.SystemHealth")
    async def test_test_database_read_success(self, mock_system_health) -> None:
        mock_system_health.objects.acount = AsyncMock(return_value=5)

        status, error = await DatabaseHealthService.test_database_read()

        assert status is True
        assert error is None
        mock_system_health.objects.acount.assert_called_once()

    @patch("apps.ping_app.v1.services.database_health_services.SystemHealth")
    async def test_test_database_read_exception(self, mock_system_health) -> None:
        mock_system_health.objects.acount = AsyncMock(side_effect=Exception("DB read failed"))

        status, error = await DatabaseHealthService.test_database_read()

        assert status is False
        assert "DB read failed" in error
        mock_system_health.objects.acount.assert_called_once()
