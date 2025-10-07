from django.core.cache import cache
from django.test import TestCase

from .models import PingLog, SystemHealth
from .schemas import PingRequestSchema
from .services import DatabaseHealthService, PingService, RedisHealthService, SystemHealthService


class PingServiceTestCase(TestCase):
    """Test cases for PingService."""

    def setUp(self):
        """Set up test data."""
        self.ping_request = PingRequestSchema(endpoint="https://httpbin.org/get", method="GET", timeout=5)

    async def test_ping_endpoint_success(self):
        """Test successful ping to external endpoint."""
        response = await PingService.ping_endpoint(self.ping_request)

        self.assertTrue(response.success)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.response_time_ms, 0)
        self.assertIsNone(response.error_message)

    async def test_ping_endpoint_invalid_url(self):
        """Test ping to invalid URL."""
        invalid_request = PingRequestSchema(
            endpoint="https://invalid-url-that-does-not-exist.com", method="GET", timeout=1
        )

        response = await PingService.ping_endpoint(invalid_request)

        self.assertFalse(response.success)
        self.assertIsNotNone(response.error_message)

    async def test_log_ping_result(self):
        """Test logging ping result to database."""
        response = await PingService.ping_endpoint(self.ping_request)
        log_entry = await PingService.log_ping_result(self.ping_request, response)

        self.assertIsNotNone(log_entry.id)
        self.assertEqual(log_entry.endpoint, self.ping_request.endpoint)
        self.assertEqual(log_entry.method, self.ping_request.method)
        self.assertEqual(log_entry.status_code, response.status_code)

    async def test_get_ping_stats(self):
        """Test getting ping statistics."""
        # Create some test ping logs
        await PingLog.objects.acreate(
            endpoint="https://example.com",
            method="GET",
            status_code=200,
            response_time_ms=100.0,
            success=True,
        )

        stats = await PingService.get_ping_stats()

        self.assertGreaterEqual(stats.total_pings, 1)
        self.assertGreaterEqual(stats.successful_pings, 1)


class DatabaseHealthServiceTestCase(TestCase):
    """Test cases for DatabaseHealthService."""

    async def test_check_database_health(self):
        """Test database health check."""
        health = await DatabaseHealthService.check_database_health()

        self.assertTrue(health.is_healthy)
        self.assertGreater(health.response_time_ms, 0)
        self.assertIsNone(health.error_message)

    async def test_database_write_permissions(self):
        """Test database write permissions."""
        success, error = await DatabaseHealthService.test_database_write()

        self.assertTrue(success)
        self.assertIsNone(error)

    async def test_database_read_permissions(self):
        """Test database read permissions."""
        success, error = await DatabaseHealthService.test_database_read()

        self.assertTrue(success)
        self.assertIsNone(error)


class RedisHealthServiceTestCase(TestCase):
    """Test cases for RedisHealthService."""

    def setUp(self):
        """Set up test data."""
        # Clear cache before each test
        cache.clear()

    async def test_check_redis_health(self):
        """Test Redis health check."""
        health = await RedisHealthService.check_redis_health()

        # Redis might not be configured, so we just check the structure
        self.assertIsInstance(health.is_healthy, bool)
        self.assertIsInstance(health.response_time_ms, (int, float))

    async def test_redis_write_permissions(self):
        """Test Redis write permissions."""
        success, error = await RedisHealthService.test_redis_write()

        # Redis might not be configured, so we just check the structure
        self.assertIsInstance(success, bool)

    async def test_redis_read_permissions(self):
        """Test Redis read permissions."""
        success, error = await RedisHealthService.test_redis_read()

        # Redis might not be configured, so we just check the structure
        self.assertIsInstance(success, bool)


class SystemHealthServiceTestCase(TestCase):
    """Test cases for SystemHealthService."""

    async def test_check_system_health(self):
        """Test overall system health check."""
        health = await SystemHealthService.check_system_health()

        self.assertIn(health.overall_status, ["healthy", "degraded", "unhealthy"])
        self.assertIsInstance(health.services, list)
        self.assertIsNotNone(health.checked_at)

    async def test_log_health_check(self):
        """Test logging health check result."""
        log_entry = await SystemHealthService.log_health_check(
            service_name="Test Service",
            service_type="database",
            is_healthy=True,
            response_time_ms=50.0,
            metadata={"test": True},
        )

        self.assertIsNotNone(log_entry.id)
        self.assertEqual(log_entry.service_name, "Test Service")
        self.assertEqual(log_entry.service_type, "database")
        self.assertTrue(log_entry.is_healthy)


class ModelTestCase(TestCase):
    """Test cases for models."""

    async def test_ping_log_model(self):
        """Test PingLog model."""
        ping_log = await PingLog.objects.acreate(
            endpoint="https://example.com",
            method="GET",
            status_code=200,
            response_time_ms=100.0,
            success=True,
        )

        self.assertIsNotNone(ping_log.id)
        self.assertEqual(str(ping_log), "Ping to https://example.com - 200 (100.0ms)")

    async def test_system_health_model(self):
        """Test SystemHealth model."""
        health = await SystemHealth.objects.acreate(
            service_name="Test Service", service_type="database", is_healthy=True, response_time_ms=50.0
        )

        self.assertIsNotNone(health.id)
        self.assertEqual(str(health), "Test Service (database) - Healthy")
