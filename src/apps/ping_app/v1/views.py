from typing import Any, Dict, List

from ninja import Router

from common.base_schemas import create_api_response_schema

from .schemas import (
    DatabaseHealthSchema,
    HealthCheckResponseSchema,
    PingLogSchema,
    PingRequestSchema,
    PingResponseSchema,
    PingStatsSchema,
    RedisHealthSchema,
    SystemStatusSchema,
)
from .services import DatabaseHealthService, PingService, RedisHealthService, SystemHealthService

router = Router()


@router.get("/", response=create_api_response_schema(Dict[str, str]))
async def ping(request):
    """Basic ping endpoint to test API connectivity."""
    request.logger.info("Basic ping endpoint accessed")

    return {
        "data": {"message": "pong", "status": "healthy"},
        "trace_id": str(request.trace_id),
        "error": {},
    }


@router.post("/endpoint/", response=create_api_response_schema(PingResponseSchema))
async def ping_endpoint(request, payload: PingRequestSchema):
    """Ping an external endpoint and log the result."""
    request.logger.info(f"Pinging endpoint: {payload.endpoint} with method: {payload.method}")

    try:
        # Perform the ping
        ping_response = await PingService.ping_endpoint(payload)

        # Log the result to database
        await PingService.log_ping_result(payload, ping_response)

        # Log the operation
        if ping_response.success:
            request.logger.info(
                f"Successfully pinged {payload.endpoint} - Status: {ping_response.status_code}, Time: {ping_response.response_time_ms:.2f}ms"
            )
        else:
            request.logger.warning(
                f"Failed to ping {payload.endpoint} - Status: {ping_response.status_code}, Error: {ping_response.error_message}"
            )

        return {
            "data": ping_response,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception(f"Error pinging endpoint {payload.endpoint}")
        raise


@router.get("/logs/", response=create_api_response_schema(List[PingLogSchema]))
async def get_ping_logs(request, limit: int = 100):
    """Get recent ping logs."""
    request.logger.info(f"Retrieving ping logs with limit: {limit}")

    try:
        logs = await PingService.get_ping_logs(limit)
        request.logger.info(f"Retrieved {len(logs)} ping logs")

        return {
            "data": logs,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error retrieving ping logs")
        raise


@router.get("/stats/", response=create_api_response_schema(PingStatsSchema))
async def get_ping_stats(request):
    """Get ping statistics."""
    request.logger.info("Retrieving ping statistics")

    try:
        stats = await PingService.get_ping_stats()
        request.logger.info(
            f"Retrieved ping stats - Total: {stats.total_pings}, Success Rate: {stats.last_24h_success_rate:.2f}%"
        )

        return {
            "data": stats,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error retrieving ping statistics")
        raise


@router.get("/health/", response=create_api_response_schema(SystemStatusSchema))
async def system_health(request):
    """Get overall system health status."""
    request.logger.info("Performing system health check")

    try:
        health_status = await SystemHealthService.check_system_health()

        # Log the health check
        for service in health_status.services:
            await SystemHealthService.log_health_check(
                service_name=service.service_name,
                service_type=service.service_type,
                is_healthy=service.is_healthy,
                response_time_ms=service.response_time_ms,
                error_message=service.error_message,
                metadata=service.metadata,
            )

        request.logger.info(f"System health check completed - Status: {health_status.overall_status}")

        return {
            "data": health_status,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error performing system health check")
        raise


@router.get("/health/database/", response=create_api_response_schema(DatabaseHealthSchema))
async def database_health(request):
    """Check database health and permissions."""
    request.logger.info("Performing database health check")

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
                "read_test": read_success,
                "write_test": write_success,
            },
        )

        if db_health.is_healthy:
            request.logger.info(
                f"Database health check passed - Response time: {db_health.response_time_ms:.2f}ms"
            )
        else:
            request.logger.warning(f"Database health check failed - {db_health.error_message}")

        return {
            "data": db_health,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error performing database health check")
        raise


@router.get("/health/redis/", response=create_api_response_schema(RedisHealthSchema))
async def redis_health(request):
    """Check Redis health and permissions."""
    request.logger.info("Performing Redis health check")

    try:
        # Check basic connectivity
        redis_health = await RedisHealthService.check_redis_health()

        # Test read permissions
        read_success, read_error = await RedisHealthService.test_redis_read()
        if not read_success:
            redis_health.error_message = (
                f"{redis_health.error_message or ''} Read test failed: {read_error}".strip()
            )
            redis_health.is_healthy = False

        # Test write permissions
        write_success, write_error = await RedisHealthService.test_redis_write()
        if not write_success:
            redis_health.error_message = (
                f"{redis_health.error_message or ''} Write test failed: {write_error}".strip()
            )
            redis_health.is_healthy = False

        # Log the health check
        await SystemHealthService.log_health_check(
            service_name="Redis",
            service_type="redis",
            is_healthy=redis_health.is_healthy,
            response_time_ms=redis_health.response_time_ms,
            error_message=redis_health.error_message,
            metadata={
                "redis_version": redis_health.redis_version,
                "memory_usage": redis_health.memory_usage,
                "connected_clients": redis_health.connected_clients,
                "read_test": read_success,
                "write_test": write_success,
            },
        )

        if redis_health.is_healthy:
            request.logger.info(
                f"Redis health check passed - Response time: {redis_health.response_time_ms:.2f}ms"
            )
        else:
            request.logger.warning(f"Redis health check failed - {redis_health.error_message}")

        return {
            "data": redis_health,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error performing Redis health check")
        raise


@router.post("/health/database/test-write/", response=create_api_response_schema(Dict[str, Any]))
async def test_database_write(request):
    """Test database write permissions specifically."""
    request.logger.info("Testing database write permissions")

    try:
        success, error_message = await DatabaseHealthService.test_database_write()

        result = {
            "success": success,
            "error_message": error_message,
            "test_type": "database_write",
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


@router.post("/health/database/test-read/", response=create_api_response_schema(Dict[str, Any]))
async def test_database_read(request):
    """Test database read permissions specifically."""
    request.logger.info("Testing database read permissions")

    try:
        success, error_message = await DatabaseHealthService.test_database_read()

        result = {
            "success": success,
            "error_message": error_message,
            "test_type": "database_read",
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


@router.post("/health/redis/test-write/", response=create_api_response_schema(Dict[str, Any]))
async def test_redis_write(request):
    """Test Redis write permissions specifically."""
    request.logger.info("Testing Redis write permissions")

    try:
        success, error_message = await RedisHealthService.test_redis_write()

        result = {
            "success": success,
            "error_message": error_message,
            "test_type": "redis_write",
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Redis write test passed")
        else:
            request.logger.warning(f"Redis write test failed - {error_message}")

        return {
            "data": result,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error testing Redis write permissions")
        raise


@router.post("/health/redis/test-read/", response=create_api_response_schema(Dict[str, Any]))
async def test_redis_read(request):
    """Test Redis read permissions specifically."""
    request.logger.info("Testing Redis read permissions")

    try:
        success, error_message = await RedisHealthService.test_redis_read()

        result = {
            "success": success,
            "error_message": error_message,
            "test_type": "redis_read",
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Redis read test passed")
        else:
            request.logger.warning(f"Redis read test failed - {error_message}")

        return {
            "data": result,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception("Error testing Redis read permissions")
        raise
