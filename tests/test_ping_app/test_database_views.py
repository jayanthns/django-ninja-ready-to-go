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
    async def test_database_ddl_failure_returns_unhealthy(self, mock_sync_to_async) -> None:
        req = await self._make_request()

        # simulate failed DDL run returning (False, error_message, None)
        mock_sync_to_async.return_value = AsyncMock(return_value=(False, "DDL failed", None))

        resp = await views.test_database_ddl(req)

        assert resp["data"]["success"] is False
        assert resp["data"]["status"] == "unhealthy"
        assert resp["data"]["error_message"] == "DDL failed"

    @patch("asgiref.sync.sync_to_async")
    async def test_database_ddl_raises_exception(self, mock_sync_to_async) -> None:
        req = await self._make_request()

        # simulate exception during DDL run
        mock_sync_to_async.return_value = AsyncMock(side_effect=Exception("DDL explosion"))

        import pytest

        with pytest.raises(Exception) as exc:
            await views.test_database_ddl(req)

        assert "DDL explosion" in str(exc.value)

    @patch("django.db.connection")
    async def test_database_ddl_inner_logic_coverage(self, mock_connection) -> None:
        """
        Test the inner logic of test_database_ddl without mocking sync_to_async.
        This ensures the actual DDL SQL generation code is executed and covered.
        """
        req = await self._make_request()

        # Mock the cursor and its behavior
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [5]  # Return 5 records count
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # We don't mock sync_to_async here, so it runs the real inner function
        # The inner function uses the mocked connection/cursor
        resp = await views.test_database_ddl(req)

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
    async def test_list_database_tables_inner_logic_coverage(self, mock_connection) -> None:
        """
        Test the inner logic of list_database_tables without mocking sync_to_async.
        This ensures the actual SQL generation and result parsing code is executed.
        """
        req = await self._make_request()

        # Mock the cursor and its results
        mock_cursor = MagicMock()
        # Mock return value for fetchall: list of tuples (table_name, table_type, rows, size_mb)
        mock_cursor.fetchall.return_value = [
            ("users", "BASE TABLE", 100, 1.5),
            ("auth_group", "BASE TABLE", 5, 0.1),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Execute the view without mocking sync_to_async
        resp = await views.list_database_tables(req)

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
    async def test_list_database_tables_raises_exception(self, mock_sync_to_async) -> None:
        req = await self._make_request()

        # simulate exception during table listing
        mock_sync_to_async.return_value = AsyncMock(side_effect=Exception("table list error"))

        import pytest

        with pytest.raises(Exception) as exc:
            await views.list_database_tables(req)

        assert "table list error" in str(exc.value)

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
    async def test_get_database_info_raises_exception(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.check_database_health = AsyncMock(side_effect=Exception("db info error"))

        import pytest

        with pytest.raises(Exception) as exc:
            await views.get_database_info(req)

        assert "db info error" in str(exc.value)
        mock_db_svc.check_database_health.assert_awaited_once()

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_write_post_endpoint(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_write = AsyncMock(return_value=(True, None))

        resp = await views.test_database_write_post(req)

        assert resp["data"]["success"] is True

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_write_post_failure(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_write = AsyncMock(return_value=(False, "write failed"))

        resp = await views.test_database_write_post(req)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "write failed"

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_write_post_exception(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_write = AsyncMock(side_effect=Exception("write explosion"))

        import pytest

        with pytest.raises(Exception) as exc:
            await views.test_database_write_post(req)

        assert "write explosion" in str(exc.value)

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_read_post_endpoint(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_read = AsyncMock(return_value=(False, "fail"))

        resp = await views.test_database_read_post(req)

        assert resp["data"]["success"] is False
        assert resp["data"]["error_message"] == "fail"

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_read_post_success(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_read = AsyncMock(return_value=(True, None))

        resp = await views.test_database_read_post(req)

        assert resp["data"]["success"] is True

    @patch("apps.ping_app.v1.views.database_views.DatabaseHealthService")
    async def test_test_database_read_post_exception(self, mock_db_svc) -> None:
        req = await self._make_request()

        mock_db_svc.test_database_read = AsyncMock(side_effect=Exception("read explosion"))

        import pytest

        with pytest.raises(Exception) as exc:
            await views.test_database_read_post(req)

        assert "read explosion" in str(exc.value)

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
