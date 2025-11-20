from datetime import datetime
from typing import Any, Dict, Optional

from ..models import SystemHealth
from ..schemas import HealthCheckResponseSchema, SystemStatusSchema
from .cache_health_services import CacheHealthService
from .database_health_services import DatabaseHealthService


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
        cache_health = await CacheHealthService.check_cache_health()
        services.append(
            HealthCheckResponseSchema(
                service_name="Redis",
                service_type="redis",
                is_healthy=cache_health.is_healthy,
                response_time_ms=cache_health.response_time_ms,
                error_message=cache_health.error_message,
                metadata={
                    "redis_version": cache_health.redis_version,
                    "memory_usage": cache_health.memory_usage,
                    "connected_clients": cache_health.connected_clients,
                },
            )
        )

        if not cache_health.is_healthy:
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
