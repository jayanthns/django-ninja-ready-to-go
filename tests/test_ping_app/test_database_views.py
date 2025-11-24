from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.ping_app.v1.views import database_views as views


@pytest.mark.asyncio
class TestDatabaseViews:

    @pytest.fixture
    def mock_request(self):
        """Fixture to create a mock request object."""
        req = MagicMock()
        req.logger = MagicMock()
        req.trace_id = "trace-123"
        req.timestamp = 123456
        return req

    async def _assert_endpoint_raises(
        self, endpoint_func, mock_service, method_name, error_msg, mock_request
    ):
        """Helper to test exception raising in endpoints."""
        getattr(mock_service, method_name).side_effect = Exception(error_msg)

        with pytest.raises(Exception) as exc:
            await endpoint_func(mock_request)

        assert error_msg in str(exc.value)

    @patch("apps.ping_app.v1.views.database_views.SystemHealthService")
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_ping_database_all_success(self, mock_db_svc, mock_system_health, mock_request) -> None:
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

        resp = await views.ping_database(mock_request)

        assert "data" in resp
        assert resp["data"].is_healthy is True
        mock_db_svc.check_database_health.assert_awaited_once()
        mock_system_health.log_health_check.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.SystemHealthService")
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_ping_database_read_failure_marks_unhealthy(
        self, mock_db_svc, mock_system_health, mock_request
    ) -> None:
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

        resp = await views.ping_database(mock_request)

        assert resp["data"].is_healthy is False
        assert "Read test failed" in resp["data"].error_message
        mock_system_health.log_health_check.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.SystemHealthService")
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_ping_database_write_failure_marks_unhealthy(
        self, mock_db_svc, mock_system_health, mock_request
    ) -> None:
        db_health = MagicMock()
        db_health.is_healthy = True
        db_health.response_time_ms = 10.0
        db_health.error_message = None

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)
        mock_db_svc.test_database_read = AsyncMock(return_value=(True, None))
        mock_db_svc.test_database_write = AsyncMock(return_value=(False, "write failed"))
        mock_system_health.log_health_check = AsyncMock()

        resp = await views.ping_database(mock_request)

        assert resp["data"].is_healthy is False
        assert "Write test failed" in resp["data"].error_message
        mock_system_health.log_health_check.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.SystemHealthService")
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_ping_database_raises_exception(
        self, mock_db_svc, mock_system_health, mock_request
    ) -> None:
        await self._assert_endpoint_raises(
            views.ping_database, mock_db_svc, "check_database_health", "boom", mock_request
        )

    @patch("asgiref.sync.sync_to_async")
    async def test_database_ddl_success(self, mock_sync_to_async, mock_request) -> None:
        # simulate successful DDL run returning (True, None, count)
        mock_sync_to_async.return_value = AsyncMock(return_value=(True, None, 3))

        resp = await views.test_database_ddl(mock_request)

        assert resp["data"]["success"] is True
        assert resp["data"]["record_count"] == 3

    @patch("asgiref.sync.sync_to_async")
    async def test_database_ddl_failure_returns_unhealthy(self, mock_sync_to_async, mock_request) -> None:
        # simulate failed DDL run returning (False, error_message, None)
        mock_sync_to_async.return_value = AsyncMock(return_value=(False, "DDL failed", None))

        resp = await views.test_database_ddl(mock_request)

        assert resp["data"]["success"] is False
        assert resp["data"]["status"] == "unhealthy"
        assert resp["data"]["error_message"] == "DDL failed"

    @patch("asgiref.sync.sync_to_async")
    async def test_database_ddl_raises_exception(self, mock_sync_to_async, mock_request) -> None:
        # simulate exception during DDL run
        mock_sync_to_async.return_value = AsyncMock(side_effect=Exception("DDL explosion"))

        with pytest.raises(Exception) as exc:
            await views.test_database_ddl(mock_request)

        assert "DDL explosion" in str(exc.value)

    @patch("django.db.connection")
    async def test_database_ddl_inner_logic_coverage(self, mock_connection, mock_request) -> None:
        """
        Test the inner logic of test_database_ddl without mocking sync_to_async.
        This ensures the actual DDL SQL generation code is executed and covered.
        """
        # Mock the cursor and its behavior
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [5]  # Return 5 records count
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # We don't mock sync_to_async here, so it runs the real inner function
        # The inner function uses the mocked connection/cursor
        resp = await views.test_database_ddl(mock_request)

        assert resp["data"]["success"] is True
        assert resp["data"]["record_count"] == 5

        # Verify that expected SQL commands were executed
        # We check for the presence of key SQL commands in the calls
        calls = mock_cursor.execute.call_args_list
        assert len(calls) >= 4  # CREATE, ALTER, INSERT, SELECT, DELETE (at least some of them)

        # Check for specific SQL fragments to ensure logic ran
        sql_statements = [call.args[0] for call in calls]
        assert any("CREATE TEMPORARY TABLE" in sql for sql in sql_statements)
        assert any("ALTER TABLE" in sql for sql in sql_statements)
        assert any("INSERT INTO" in sql for sql in sql_statements)
        assert any("SELECT COUNT(*)" in sql for sql in sql_statements)
        assert any("DELETE FROM" in sql for sql in sql_statements)

    @patch("django.db.connection")
    async def test_list_database_tables_inner_logic_coverage(self, mock_connection, mock_request) -> None:
        """
        Test the inner logic of list_database_tables without mocking sync_to_async.
        This ensures the actual SQL generation and result parsing code is executed.
        """
        # Mock the cursor and its results
        mock_cursor = MagicMock()
        # Mock return value for fetchall: list of tuples (table_name, table_type, rows, size_mb)
        mock_cursor.fetchall.return_value = [
            ("users", "BASE TABLE", 100, 1.5),
            ("auth_group", "BASE TABLE", 5, 0.1),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Execute the view without mocking sync_to_async
        resp = await views.list_database_tables(mock_request)

        assert resp["data"]["status"] == "healthy"
        assert resp["data"]["total_tables"] == 2
        assert len(resp["data"]["tables"]) == 2

        # Verify the parsed data
        first_table = resp["data"]["tables"][0]
        assert first_table["name"] == "users"
        assert first_table["type"] == "BASE TABLE"
        assert first_table["rows"] == 100
        assert first_table["size_mb"] == 1.5

        # Verify SQL execution
        mock_cursor.execute.assert_called_once()
        sql_arg = mock_cursor.execute.call_args[0][0]
        assert "SELECT" in sql_arg
        assert "information_schema.tables" in sql_arg
        assert "pg_stat_user_tables" in sql_arg

    @patch("asgiref.sync.sync_to_async")
    async def test_list_database_tables_raises_exception(self, mock_sync_to_async, mock_request) -> None:
        # simulate exception during table listing
        mock_sync_to_async.return_value = AsyncMock(side_effect=Exception("table list error"))

        with pytest.raises(Exception) as exc:
            await views.list_database_tables(mock_request)

        assert "table list error" in str(exc.value)

    @patch("asgiref.sync.sync_to_async")
    async def test_list_database_tables_returns_list(self, mock_sync_to_async, mock_request) -> None:
        mock_sync_to_async.return_value = AsyncMock(
            return_value=[("t1", "BASE TABLE", 10, 0.1), ("t2", "BASE TABLE", 0, 0.0)]
        )

        resp = await views.list_database_tables(mock_request)

        assert resp["data"]["total_tables"] == 2
        assert len(resp["data"]["tables"]) == 2

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_get_database_info_builds_dict(self, mock_db_svc, mock_request) -> None:
        db_health = MagicMock()
        db_health.is_healthy = True
        db_health.response_time_ms = 5.0
        db_health.database_name = "mydb"
        db_health.connection_count = 7

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)

        resp = await views.get_database_info(mock_request)

        assert resp["data"]["database"]["name"] == "mydb"
        assert resp["data"]["connection"]["count"] == 7

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_get_database_info_raises_exception(self, mock_db_svc, mock_request) -> None:
        await self._assert_endpoint_raises(
            views.get_database_info, mock_db_svc, "check_database_health", "db info error", mock_request
        )

    # Test database read/write endpoints - both GET and POST versions exist
    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_read_get_success(self, mock_db_svc, mock_request) -> None:
        """Test GET endpoint for database read."""
        mock_db_svc.test_database_read = AsyncMock(return_value=(True, None))

        resp = await views.test_database_read(mock_request)

        assert resp["data"]["success"] is True
        assert resp["data"]["status"] == "healthy"
        assert resp["trace_id"] == "trace-123"
        mock_db_svc.test_database_read.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_read_get_failure(self, mock_db_svc, mock_request) -> None:
        """Test GET endpoint for database read failure."""
        mock_db_svc.test_database_read = AsyncMock(return_value=(False, "db read error"))

        resp = await views.test_database_read(mock_request)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "db read error"
        assert resp["data"]["status"] == "unhealthy"
        mock_db_svc.test_database_read.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_read_get_raises(self, mock_db_svc, mock_request) -> None:
        """Test GET endpoint for database read exception."""
        await self._assert_endpoint_raises(
            views.test_database_read, mock_db_svc, "test_database_read", "boom", mock_request
        )

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_read_post_success(self, mock_db_svc, mock_request) -> None:
        """Test POST endpoint for database read."""
        mock_db_svc.test_database_read = AsyncMock(return_value=(True, None))

        resp = await views.test_database_read_post(mock_request)

        assert resp["data"]["success"] is True

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_read_post_failure(self, mock_db_svc, mock_request) -> None:
        """Test POST endpoint for database read failure."""
        mock_db_svc.test_database_read = AsyncMock(return_value=(False, "fail"))

        resp = await views.test_database_read_post(mock_request)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "fail"

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_read_post_exception(self, mock_db_svc, mock_request) -> None:
        """Test POST endpoint for database read exception."""
        await self._assert_endpoint_raises(
            views.test_database_read_post, mock_db_svc, "test_database_read", "read explosion", mock_request
        )

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_write_get_success(self, mock_db_svc, mock_request) -> None:
        """Test GET endpoint for database write."""
        mock_db_svc.test_database_write = AsyncMock(return_value=(True, None))

        resp = await views.test_database_write(mock_request)

        assert resp["data"]["success"] is True
        assert resp["data"]["status"] == "healthy"
        mock_db_svc.test_database_write.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_write_get_failure(self, mock_db_svc, mock_request) -> None:
        """Test GET endpoint for database write failure."""
        mock_db_svc.test_database_write = AsyncMock(return_value=(False, "write error"))

        resp = await views.test_database_write(mock_request)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "write error"
        assert resp["data"]["status"] == "unhealthy"
        mock_db_svc.test_database_write.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_write_get_raises(self, mock_db_svc, mock_request) -> None:
        """Test GET endpoint for database write exception."""
        await self._assert_endpoint_raises(
            views.test_database_write, mock_db_svc, "test_database_write", "boom write", mock_request
        )

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_write_post_success(self, mock_db_svc, mock_request) -> None:
        """Test POST endpoint for database write."""
        mock_db_svc.test_database_write = AsyncMock(return_value=(True, None))

        resp = await views.test_database_write_post(mock_request)

        assert resp["data"]["success"] is True

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_write_post_failure(self, mock_db_svc, mock_request) -> None:
        """Test POST endpoint for database write failure."""
        mock_db_svc.test_database_write = AsyncMock(return_value=(False, "write failed"))

        resp = await views.test_database_write_post(mock_request)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "write failed"

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_database_write_post_exception(self, mock_db_svc, mock_request) -> None:
        """Test POST endpoint for database write exception."""
        await self._assert_endpoint_raises(
            views.test_database_write_post,
            mock_db_svc,
            "test_database_write",
            "write explosion",
            mock_request,
        )
