from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.ping_app.v1.services.system_health_services import SystemHealthService


@pytest.mark.asyncio
class TestSystemHealthService:

    @patch("apps.ping_app.v1.services.system_health_services.DatabaseHealthService")
    @patch("apps.ping_app.v1.services.system_health_services.CacheHealthService")
    async def test_check_system_health_all_healthy(self, mock_cache_svc, mock_db_svc) -> None:
        # Mock database health
        db_health = MagicMock()
        db_health.is_healthy = True
        db_health.response_time_ms = 10.0
        db_health.error_message = None
        db_health.connection_count = 3
        db_health.database_name = "mydb"

        # Mock cache health
        cache_health = MagicMock()
        cache_health.is_healthy = True
        cache_health.response_time_ms = 20.0
        cache_health.error_message = None
        cache_health.redis_version = "6.0.9"
        cache_health.memory_usage = "1.2M"
        cache_health.connected_clients = 5

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)
        mock_cache_svc.check_cache_health = AsyncMock(return_value=cache_health)

        result = await SystemHealthService.check_system_health()

        assert result.overall_status == "healthy"
        assert len(result.services) == 2
        # Database service metadata
        db_meta = result.services[0].metadata
        assert db_meta["connection_count"] == 3
        assert db_meta["database_name"] == "mydb"
        # Redis service metadata
        cache_meta = result.services[1].metadata
        assert cache_meta["redis_version"] == "6.0.9"
        assert cache_meta["memory_usage"] == "1.2M"

    @patch("apps.ping_app.v1.services.system_health_services.DatabaseHealthService")
    @patch("apps.ping_app.v1.services.system_health_services.CacheHealthService")
    async def test_check_system_health_degraded_when_one_unhealthy(self, mock_cache_svc, mock_db_svc) -> None:
        db_health = MagicMock()
        db_health.is_healthy = True
        db_health.response_time_ms = 5.0
        db_health.error_message = None
        db_health.connection_count = None
        db_health.database_name = None

        cache_health = MagicMock()
        cache_health.is_healthy = False
        cache_health.response_time_ms = 30.0
        cache_health.error_message = "redis down"
        cache_health.redis_version = None
        cache_health.memory_usage = None
        cache_health.connected_clients = None

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)
        mock_cache_svc.check_cache_health = AsyncMock(return_value=cache_health)

        result = await SystemHealthService.check_system_health()

        assert result.overall_status == "degraded"
        assert any(s.service_name == "Redis" and not s.is_healthy for s in result.services)

    @patch("apps.ping_app.v1.services.system_health_services.DatabaseHealthService")
    @patch("apps.ping_app.v1.services.system_health_services.CacheHealthService")
    async def test_check_system_health_unhealthy_when_all_unhealthy(
        self, mock_cache_svc, mock_db_svc
    ) -> None:
        db_health = MagicMock()
        db_health.is_healthy = False
        db_health.response_time_ms = 50.0
        db_health.error_message = "db down"
        db_health.connection_count = None
        db_health.database_name = None

        cache_health = MagicMock()
        cache_health.is_healthy = False
        cache_health.response_time_ms = 40.0
        cache_health.error_message = "redis down"
        cache_health.redis_version = None
        cache_health.memory_usage = None
        cache_health.connected_clients = None

        mock_db_svc.check_database_health = AsyncMock(return_value=db_health)
        mock_cache_svc.check_cache_health = AsyncMock(return_value=cache_health)

        result = await SystemHealthService.check_system_health()

        assert result.overall_status == "unhealthy"
        assert all(not s.is_healthy for s in result.services)

    @patch("apps.ping_app.v1.services.system_health_services.SystemHealth")
    async def test_log_health_check_creates_record(self, mock_system_health) -> None:
        mock_record = MagicMock()
        mock_system_health.objects.acreate = AsyncMock(return_value=mock_record)

        rec = await SystemHealthService.log_health_check(
            service_name="Database",
            service_type="database",
            is_healthy=True,
            response_time_ms=12.3,
            error_message=None,
            metadata={"k": "v"},
        )

        mock_system_health.objects.acreate.assert_awaited_once()
        assert rec is mock_record
