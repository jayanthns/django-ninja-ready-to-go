import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache
from django.db import connection

from .models import PingLog, SystemHealth
from .schemas import (
    DatabaseHealthSchema,
    HealthCheckResponseSchema,
    PingRequestSchema,
    PingResponseSchema,
    PingStatsSchema,
    RedisHealthSchema,
    SystemStatusSchema,
)


class PingService:
    """Service for handling ping operations and health checks."""

    @staticmethod
    async def ping_endpoint(ping_request: PingRequestSchema) -> PingResponseSchema:
        """
        Ping an external endpoint and return response details.

        Args:
            ping_request: The ping request details

        Returns:
            PingResponseSchema: Response details including timing and status
        """
        start_time = time.time()
        response_headers = {}
        error_message = None
        status_code = 0
        success = False

        try:
            timeout = aiohttp.ClientTimeout(total=ping_request.timeout)
            headers = ping_request.headers or {}

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=ping_request.method, url=ping_request.endpoint, headers=headers
                ) as response:
                    status_code = response.status
                    response_headers = dict(response.headers)
                    success = 200 <= status_code < 400

        except asyncio.TimeoutError:
            error_message = f"Request timed out after {ping_request.timeout} seconds"
        except aiohttp.ClientError as e:
            error_message = f"Client error: {str(e)}"
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"

        response_time_ms = (time.time() - start_time) * 1000

        return PingResponseSchema(
            endpoint=ping_request.endpoint,
            method=ping_request.method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            response_headers=response_headers,
        )

    @staticmethod
    async def log_ping_result(ping_request: PingRequestSchema, ping_response: PingResponseSchema) -> PingLog:
        """
        Log ping result to database.

        Args:
            ping_request: The original ping request
            ping_response: The ping response

        Returns:
            PingLog: The created ping log entry
        """
        return await PingLog.objects.acreate(
            endpoint=ping_request.endpoint,
            method=ping_request.method,
            status_code=ping_response.status_code,
            response_time_ms=ping_response.response_time_ms,
            success=ping_response.success,
            error_message=ping_response.error_message,
            request_headers=ping_request.headers or {},
            response_headers=ping_response.response_headers,
        )

    @staticmethod
    async def get_ping_logs(limit: int = 100) -> List[PingLog]:
        """
        Get recent ping logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List[PingLog]: Recent ping logs
        """
        return [log async for log in PingLog.objects.all()[:limit]]

    @staticmethod
    async def get_ping_stats() -> PingStatsSchema:
        """
        Get ping statistics.

        Returns:
            PingStatsSchema: Ping statistics
        """
        # Get all ping logs
        all_pings = [ping async for ping in PingLog.objects.all()]

        if not all_pings:
            return PingStatsSchema(
                total_pings=0,
                successful_pings=0,
                failed_pings=0,
                average_response_time_ms=0.0,
                min_response_time_ms=0.0,
                max_response_time_ms=0.0,
                last_24h_pings=0,
                last_24h_success_rate=0.0,
            )

        # Calculate basic stats
        total_pings = len(all_pings)
        successful_pings = sum(1 for ping in all_pings if ping.success)
        failed_pings = total_pings - successful_pings

        response_times = [ping.response_time_ms for ping in all_pings]
        average_response_time_ms = sum(response_times) / len(response_times)
        min_response_time_ms = min(response_times)
        max_response_time_ms = max(response_times)

        # Calculate 24h stats
        from django.utils import timezone

        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        recent_pings = [ping for ping in all_pings if ping.created_at >= twenty_four_hours_ago]
        last_24h_pings = len(recent_pings)
        last_24h_successful = sum(1 for ping in recent_pings if ping.success)
        last_24h_success_rate = (last_24h_successful / last_24h_pings * 100) if last_24h_pings > 0 else 0.0

        return PingStatsSchema(
            total_pings=total_pings,
            successful_pings=successful_pings,
            failed_pings=failed_pings,
            average_response_time_ms=average_response_time_ms,
            min_response_time_ms=min_response_time_ms,
            max_response_time_ms=max_response_time_ms,
            last_24h_pings=last_24h_pings,
            last_24h_success_rate=last_24h_success_rate,
        )


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
            count = await SystemHealth.objects.acount()
            return True, None

        except Exception as e:
            return False, f"Database read test failed: {str(e)}"


class RedisHealthService:
    """Service for Redis health checks."""

    @staticmethod
    async def check_redis_health() -> RedisHealthSchema:
        """
        Check Redis connectivity and performance.

        Returns:
            RedisHealthSchema: Redis health status
        """
        start_time = time.time()
        error_message = None
        redis_version = None
        memory_usage = None
        connected_clients = None

        try:
            # Test Redis connection using Django cache
            test_key = "health_check_test"
            test_value = f"test_{int(time.time())}"

            # Test write
            await sync_to_async(cache.set)(test_key, test_value, timeout=10)

            # Test read
            retrieved_value = await sync_to_async(cache.get)(test_key)

            if retrieved_value != test_value:
                error_message = "Redis read/write test failed - value mismatch"
            else:
                # Clean up test key
                await sync_to_async(cache.delete)(test_key)

                # Try to get Redis info (if available)
                try:
                    # This might not work with all cache backends
                    if hasattr(cache, "_cache") and hasattr(cache._cache, "get_client"):
                        client = cache._cache.get_client()
                        if hasattr(client, "info"):
                            info = client.info()
                            redis_version = info.get("redis_version")
                            memory_usage = info.get("used_memory_human")
                            connected_clients = info.get("connected_clients")
                except Exception:
                    # Redis info not available, that's okay
                    pass

        except Exception as e:
            error_message = f"Redis connection failed: {str(e)}"

        response_time_ms = (time.time() - start_time) * 1000
        is_healthy = error_message is None

        return RedisHealthSchema(
            is_healthy=is_healthy,
            response_time_ms=response_time_ms,
            error_message=error_message,
            redis_version=redis_version,
            memory_usage=memory_usage,
            connected_clients=connected_clients,
        )

    @staticmethod
    async def test_redis_write() -> Tuple[bool, Optional[str]]:
        """
        Test Redis write permissions.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            test_key = f"write_test_{int(time.time())}"
            test_value = "test_value"

            await sync_to_async(cache.set)(test_key, test_value, timeout=60)
            retrieved_value = await sync_to_async(cache.get)(test_key)

            if retrieved_value != test_value:
                return False, "Redis write test failed - value mismatch"

            # Clean up
            await sync_to_async(cache.delete)(test_key)
            return True, None

        except Exception as e:
            return False, f"Redis write test failed: {str(e)}"

    @staticmethod
    async def test_redis_read() -> Tuple[bool, Optional[str]]:
        """
        Test Redis read permissions.

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            # Try to read a non-existent key (should return None)
            result = await sync_to_async(cache.get)("non_existent_key")
            return True, None

        except Exception as e:
            return False, f"Redis read test failed: {str(e)}"


class SystemHealthService:
    """Service for overall system health monitoring."""

    @staticmethod
    async def check_system_health() -> SystemStatusSchema:
        """
        Perform comprehensive system health check.

        Returns:
            SystemStatusSchema: Overall system health status
        """
        services = []
        overall_healthy = True

        # Check database
        db_health = await DatabaseHealthService.check_database_health()
        services.append(
            HealthCheckResponseSchema(
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
        )

        if not db_health.is_healthy:
            overall_healthy = False

        # Check Redis
        redis_health = await RedisHealthService.check_redis_health()
        services.append(
            HealthCheckResponseSchema(
                service_name="Redis",
                service_type="redis",
                is_healthy=redis_health.is_healthy,
                response_time_ms=redis_health.response_time_ms,
                error_message=redis_health.error_message,
                metadata={
                    "redis_version": redis_health.redis_version,
                    "memory_usage": redis_health.memory_usage,
                    "connected_clients": redis_health.connected_clients,
                },
            )
        )

        if not redis_health.is_healthy:
            overall_healthy = False

        # Determine overall status
        if overall_healthy:
            overall_status = "healthy"
        else:
            # Check if any services are down
            unhealthy_services = [s for s in services if not s.is_healthy]
            if len(unhealthy_services) == len(services):
                overall_status = "unhealthy"
            else:
                overall_status = "degraded"

        return SystemStatusSchema(
            overall_status=overall_status,
            services=services,
            checked_at=datetime.now(),
            uptime_seconds=None,  # Could be implemented with process uptime
        )

    @staticmethod
    async def log_health_check(
        service_name: str,
        service_type: str,
        is_healthy: bool,
        response_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SystemHealth:
        """
        Log a health check result to the database.

        Args:
            service_name: Name of the service
            service_type: Type of service
            is_healthy: Whether the service is healthy
            response_time_ms: Response time in milliseconds
            error_message: Error message if unhealthy
            metadata: Additional metadata

        Returns:
            SystemHealth: The created health check log
        """
        return await SystemHealth.objects.acreate(
            service_name=service_name,
            service_type=service_type,
            is_healthy=is_healthy,
            response_time_ms=response_time_ms,
            error_message=error_message,
            metadata=metadata or {},
        )
