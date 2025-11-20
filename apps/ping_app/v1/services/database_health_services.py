import time
from datetime import datetime
from typing import Optional, Tuple

from asgiref.sync import sync_to_async
from django.db import connection

from ..models import SystemHealth
from ..schemas import DatabaseHealthSchema


class DatabaseHealthService:
    """Service for database health checks."""

    @staticmethod
    async def check_database_health() -> DatabaseHealthSchema:
        """
        Check database connectivity and performance.

        Returns:
            DatabaseHealthSchema: Database health status
        """
        start_time = time.time()
        error_message = None
        connection_count = None
        database_name = None

        try:
            # Test database connection using sync_to_async
            def _test_db_connection():
                nonlocal database_name, connection_count
                with connection.cursor() as cursor:
                    # Simple query to test connectivity
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()

                    if result and result[0] == 1:
                        # Get connection info
                        cursor.execute("SELECT current_database()")
                        db_name = cursor.fetchone()
                        database_name = db_name[0] if db_name else None

                        # Get connection count (PostgreSQL specific)
                        try:
                            cursor.execute("SELECT count(*) FROM pg_stat_activity")
                            conn_count = cursor.fetchone()
                            connection_count = conn_count[0] if conn_count else None
                        except Exception:
                            # Not PostgreSQL or query failed
                            pass
                    else:
                        return "Database query returned unexpected result"
                    return None

            error_message = await sync_to_async(_test_db_connection)()

        except Exception as e:
            error_message = f"Database connection failed: {str(e)}"

        response_time_ms = (time.time() - start_time) * 1000
        is_healthy = error_message is None

        return DatabaseHealthSchema(
            is_healthy=is_healthy,
            response_time_ms=response_time_ms,
            error_message=error_message,
            connection_count=connection_count,
            database_name=database_name,
        )

    @staticmethod
    async def test_database_write() -> Tuple[bool, Optional[str]]:
        """
        Test database write permissions by creating a test record.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            # Create a test SystemHealth record
            test_record = await SystemHealth.objects.acreate(
                service_name="database_write_test",
                service_type="database",
                is_healthy=True,
                response_time_ms=0.0,
                metadata={"test": True, "timestamp": datetime.now().isoformat()},
            )

            # Clean up the test record
            await test_record.adelete()

            return True, None

        except Exception as e:
            return False, f"Database write test failed: {str(e)}"

    @staticmethod
    async def test_database_read() -> Tuple[bool, Optional[str]]:
        """
        Test database read permissions.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            # Try to read from SystemHealth table
            _ = await SystemHealth.objects.acount()
            return True, None

        except Exception as e:
            return False, f"Database read test failed: {str(e)}"
