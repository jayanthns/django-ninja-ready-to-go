from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.ping_app.v1.schemas import DatabaseHealthSchema


class TestCheckDbCommand:

    @patch("apps.ping_app.v1.management.commands.check_db.DatabaseHealthService.check_database_health")
    def test_check_db_healthy(self, mock_check_health, capsys):
        """Test check_db command when database is healthy."""
        # Arrange
        mock_check_health.return_value = DatabaseHealthSchema(
            is_healthy=True,
            response_time_ms=10.0,
            error_message=None,
            connection_count=5,
            database_name="test_db",
        )

        # Act
        call_command("check_db")

        # Assert
        captured = capsys.readouterr()
        assert "Checking Database health..." in captured.out
        assert "✅ Database is HEALTHY" in captured.out
        mock_check_health.assert_called_once()

    @patch("apps.ping_app.v1.management.commands.check_db.DatabaseHealthService.check_database_health")
    def test_check_db_unhealthy(self, mock_check_health, capsys):
        """Test check_db command when database is unhealthy."""
        # Arrange
        mock_check_health.return_value = DatabaseHealthSchema(
            is_healthy=False,
            response_time_ms=0.0,
            error_message="Connection failed",
            connection_count=None,
            database_name=None,
        )

        # Act & Assert
        with pytest.raises(SystemExit) as e:
            call_command("check_db")

        assert e.type == SystemExit
        assert e.value.code == 1

        captured = capsys.readouterr()
        assert "Checking Database health..." in captured.out
        assert "❌ Database is UNHEALTHY: Connection failed" in captured.out
        mock_check_health.assert_called_once()

    @patch("apps.ping_app.v1.management.commands.check_db.DatabaseHealthService.check_database_health")
    def test_check_db_exception(self, mock_check_health, capsys):
        """Test check_db command when an exception raises during health check call."""
        # Arrange
        mock_check_health.side_effect = Exception("Unexpected error")

        # Act & Assert
        with pytest.raises(SystemExit) as e:
            call_command("check_db")

        assert e.type == SystemExit
        assert e.value.code == 1

        captured = capsys.readouterr()
        assert "Checking Database health..." in captured.out
        assert "❌ Database health check failed with exception: Unexpected error" in captured.out
        mock_check_health.assert_called_once()
