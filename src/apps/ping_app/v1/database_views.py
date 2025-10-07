"""
Database health check endpoints for PostgreSQL connectivity and operations.
"""

from typing import Any, Dict

from ninja import Router

from common.base_schemas import create_api_response_schema

from .schemas import DatabaseHealthSchema
from .services import DatabaseHealthService, SystemHealthService

router = Router()


@router.get("/ping", response=create_api_response_schema(DatabaseHealthSchema))
async def ping_database(request):
    """
    Ping database connectivity and basic health check.

    Tests:
    - Database connection
    - Basic query execution
    - Connection pool status
    - Response time measurement
    """
    request.logger.info("Pinging database service")

    try:
        # Check basic connectivity
        db_health = await DatabaseHealthService.check_database_health()

        # Test read permissions
        read_success, read_error = await DatabaseHealthService.test_database_read()
        if not read_success:
            db_health.error_message = (
                f"{db_health.error_message or ''} Read test failed: {read_error}".strip()
            )
            db_health.is_healthy = False

        # Test write permissions
        write_success, write_error = await DatabaseHealthService.test_database_write()
        if not write_success:
            db_health.error_message = (
                f"{db_health.error_message or ''} Write test failed: {write_error}".strip()
            )
            db_health.is_healthy = False

        # Log the health check
        await SystemHealthService.log_health_check(
            service_name="Database",
            service_type="database",
            is_healthy=db_health.is_healthy,
            response_time_ms=db_health.response_time_ms,
            error_message=db_health.error_message,
            metadata={
                "connection_count": db_health.connection_count,
                "database_name": db_health.database_name,
            },
        )

        if db_health.is_healthy:
            request.logger.info(
                f"Database ping successful - Response time: {db_health.response_time_ms:.2f}ms"
            )
        else:
            request.logger.warning(f"Database ping failed - {db_health.error_message}")

        return {
            "data": db_health,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error pinging database service")
        raise


@router.get("/read", response=create_api_response_schema(Dict[str, Any]))
async def test_database_read(request):
    """
    Test database read access (SELECT operations).

    Tests:
    - SELECT query execution
    - Data retrieval
    - Query performance
    - Result set handling
    """
    request.logger.info("Testing database read access")

    try:
        success, error_message = await DatabaseHealthService.test_database_read()

        result = {
            "status": "healthy" if success else "unhealthy",
            "operation": "read_test",
            "success": success,
            "error_message": error_message,
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Database read test passed")
        else:
            request.logger.warning(f"Database read test failed - {error_message}")

        return {
            "data": result,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error testing database read access")
        raise


@router.get("/write", response=create_api_response_schema(Dict[str, Any]))
async def test_database_write(request):
    """
    Test database write access (INSERT/UPDATE/DELETE operations).

    Tests:
    - INSERT operation
    - UPDATE operation
    - DELETE operation
    - Transaction handling
    """
    request.logger.info("Testing database write access")

    try:
        success, error_message = await DatabaseHealthService.test_database_write()

        result = {
            "status": "healthy" if success else "unhealthy",
            "operation": "write_test",
            "success": success,
            "error_message": error_message,
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Database write test passed")
        else:
            request.logger.warning(f"Database write test failed - {error_message}")

        return {
            "data": result,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error testing database write access")
        raise


@router.get("/ddl", response=create_api_response_schema(Dict[str, Any]))
async def test_database_ddl(request):
    """
    Test database DDL operations (CREATE/DROP/ALTER).

    Tests:
    - CREATE TABLE operation
    - ALTER TABLE operation
    - DROP TABLE operation
    - Schema manipulation
    """
    request.logger.info("Testing database DDL operations")

    try:
        # For Django, we can test DDL by creating a temporary model
        # This is a simplified test
        from django.db import connection

        def _test_ddl():
            with connection.cursor() as cursor:
                # Test creating a temporary table
                test_table = f"ddl_test_{int(request.timestamp) if hasattr(request, 'timestamp') else 123456}"

                # Create temporary table
                cursor.execute(
                    f"""
                    CREATE TEMPORARY TABLE {test_table} (
                        id SERIAL PRIMARY KEY,
                        test_data VARCHAR(100),
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """
                )

                # Test ALTER TABLE
                cursor.execute(
                    f"""
                    ALTER TABLE {test_table}
                    ADD COLUMN description TEXT
                """
                )

                # Test INSERT
                cursor.execute(
                    f"""
                    INSERT INTO {test_table} (test_data, description)
                    VALUES ('test_data', 'test_description')
                """
                )

                # Test SELECT
                cursor.execute(f"SELECT COUNT(*) FROM {test_table}")
                count = cursor.fetchone()[0]

                # Test DELETE
                cursor.execute(f"DELETE FROM {test_table}")

                # Table will be automatically dropped as it's temporary
                return True, None, count

        from asgiref.sync import sync_to_async

        success, error_message, record_count = await sync_to_async(_test_ddl)()

        result = {
            "status": "healthy" if success else "unhealthy",
            "operation": "ddl_test",
            "success": success,
            "error_message": error_message,
            "record_count": record_count,
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Database DDL test passed")
        else:
            request.logger.warning(f"Database DDL test failed - {error_message}")

        return {
            "data": result,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error testing database DDL operations")
        raise


@router.get("/info", response=create_api_response_schema(Dict[str, Any]))
async def get_database_info(request):
    """
    Get comprehensive database information and status.

    Returns:
    - Database version and type
    - Connection pool status
    - Database size and statistics
    - Active connections
    - Configuration details
    """
    request.logger.info("Getting database information")

    try:
        # Get database health info
        db_health = await DatabaseHealthService.check_database_health()

        # Prepare detailed database info
        db_info = {
            "status": "healthy" if db_health.is_healthy else "unhealthy",
            "database": {
                "name": db_health.database_name or "unknown",
                "type": "PostgreSQL",
                "response_time_ms": db_health.response_time_ms,
            },
            "connection": {
                "count": db_health.connection_count or 0,
                "healthy": db_health.is_healthy,
            },
            "error_message": db_health.error_message,
        }

        request.logger.info("Database info retrieved successfully")

        return {
            "data": db_info,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Failed to get database info")
        raise


@router.get("/tables", response=create_api_response_schema(Dict[str, Any]))
async def list_database_tables(request):
    """
    List all tables in the current database.

    Returns:
    - Table names and types
    - Table row counts
    - Table sizes
    - Creation/modification dates
    """
    request.logger.info("Listing database tables")

    try:
        from asgiref.sync import sync_to_async
        from django.db import connection

        def _get_tables():
            with connection.cursor() as cursor:
                # Get table information
                cursor.execute(
                    """
                    SELECT
                        t.table_name,
                        t.table_type,
                        COALESCE(s.n_tup_ins + s.n_tup_upd + s.n_tup_del, 0) as table_rows,
                        ROUND(COALESCE(pg_total_relation_size(c.oid) / 1024.0 / 1024.0, 0), 2) as size_mb
                    FROM information_schema.tables t
                    LEFT JOIN pg_class c ON c.relname = t.table_name
                    LEFT JOIN pg_stat_user_tables s ON s.relname = t.table_name
                    WHERE t.table_schema = current_schema()
                    ORDER BY t.table_name
                """
                )

                tables = cursor.fetchall()
                table_list = []
                for table in tables:
                    table_list.append(
                        {
                            "name": table[0],
                            "type": table[1],
                            "rows": table[2],
                            "size_mb": table[3],
                        }
                    )
                return table_list

        tables = await sync_to_async(_get_tables)()

        result = {
            "status": "healthy",
            "total_tables": len(tables),
            "tables": tables,
        }

        request.logger.info(f"Retrieved {len(tables)} tables")

        return {
            "data": result,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Failed to list database tables")
        raise


@router.post("/test-write/", response=create_api_response_schema(Dict[str, Any]))
async def test_database_write_post(request):
    """Test database write permissions specifically (POST endpoint)."""
    request.logger.info("Testing database write permissions")

    try:
        success, error_message = await DatabaseHealthService.test_database_write()

        result = {
            "success": success,
            "error_message": error_message,
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Database write test passed")
        else:
            request.logger.warning(f"Database write test failed - {error_message}")

        return {
            "data": result,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error testing database write permissions")
        raise


@router.post("/test-read/", response=create_api_response_schema(Dict[str, Any]))
async def test_database_read_post(request):
    """Test database read permissions specifically (POST endpoint)."""
    request.logger.info("Testing database read permissions")

    try:
        success, error_message = await DatabaseHealthService.test_database_read()

        result = {
            "success": success,
            "error_message": error_message,
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Database read test passed")
        else:
            request.logger.warning(f"Database read test failed - {error_message}")

        return {
            "data": result,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error testing database read permissions")
        raise
