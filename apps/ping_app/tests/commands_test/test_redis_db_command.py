from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.ping_app.v1.schemas import RedisHealthSchema


class TestCheckRedisCommand:

    @patch("apps.ping_app.v1.management.commands.check_redis.CacheHealthService.check_cache_health")
    def test_check_redis_healthy(self, mock_check_health, capsys):
        """Test check_redis command when redis is healthy."""
        # Arrange
        mock_check_health.return_value = RedisHealthSchema(
            is_healthy=True, response_time_ms=5.0, error_message=None
        )

        # Act
        call_command("check_redis")

        # Assert
        captured = capsys.readouterr()
        assert "Checking Redis health..." in captured.out
        assert "✅ Redis is HEALTHY" in captured.out
        mock_check_health.assert_called_once()

    @patch("apps.ping_app.v1.management.commands.check_redis.CacheHealthService.check_cache_health")
    def test_check_redis_unhealthy(self, mock_check_health, capsys):
        """Test check_redis command when redis is unhealthy."""
        # Arrange
        mock_check_health.return_value = RedisHealthSchema(
            is_healthy=False, response_time_ms=0.0, error_message="Redis connection failed"
        )

        # Act & Assert
        with pytest.raises(SystemExit) as e:
            call_command("check_redis")

        assert e.type == SystemExit
        assert e.value.code == 1

        captured = capsys.readouterr()
        assert "Checking Redis health..." in captured.out
        assert "❌ Redis is UNHEALTHY: Redis connection failed" in captured.out
        mock_check_health.assert_called_once()

    @patch("apps.ping_app.v1.management.commands.check_redis.CacheHealthService.check_cache_health")
    def test_check_redis_exception(self, mock_check_health, capsys):
        """Test check_redis command when an exception raises during health check call."""
        # Arrange
        mock_check_health.side_effect = Exception("Unexpected Redis error")

        # Act & Assert
        with pytest.raises(SystemExit) as e:
            call_command("check_redis")

        assert e.type == SystemExit
        assert e.value.code == 1

        captured = capsys.readouterr()
        assert "Checking Redis health..." in captured.out
        assert "❌ Redis health check failed with exception: Unexpected Redis error" in captured.out
        mock_check_health.assert_called_once()
