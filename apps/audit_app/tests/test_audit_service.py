from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.animals_app.v1.models import Animal
from apps.audit_app.v1.services import AuditService
from common.enums import AuditAction


@pytest.mark.asyncio
class TestAuditService:
    @patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock)
    async def test_log_event_generic(self, mock_acreate):
        """Test generic event logging with mock."""
        # Setup mock return value
        mock_log = MagicMock()
        mock_log.action = AuditAction.LOGIN
        mock_log.ip_address = "127.0.0.1"
        mock_log.actor_id = "123"
        mock_log.actor_email = "test@example.com"
        mock_acreate.return_value = mock_log

        log = await AuditService.log_event(
            action=AuditAction.LOGIN,
            target_model="auth.User",
            target_object_id="1",
            ip_address="127.0.0.1",
            actor_id="123",
            actor_email="test@example.com",
        )

        mock_acreate.assert_called_once_with(
            actor_id="123",
            actor_email="test@example.com",
            action=AuditAction.LOGIN,
            target_model="auth.User",
            target_object_id="1",
            changes={},
            ip_address="127.0.0.1",
            user_agent=None,
        )
        assert log.action == AuditAction.LOGIN
        assert log.ip_address == "127.0.0.1"
        assert log.actor_id == "123"
        assert log.actor_email == "test@example.com"

    @patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock)
    async def test_log_create_helper(self, mock_acreate):
        """Test log_create helper with mock."""
        # Create a dummy animal instance without saving to DB
        animal = Animal(name="AuditDog", species="Dog", age=3)
        animal.id = 1  # Manually set ID

        mock_log = MagicMock()
        mock_log.action = AuditAction.CREATE
        mock_log.target_model = "apps_animals_app_v1.animal"
        mock_log.target_object_id = "1"
        mock_log.changes = {"name": "AuditDog"}
        mock_acreate.return_value = mock_log

        log = await AuditService.log_create(instance=animal, actor_id="999", changes={"name": "AuditDog"})

        mock_acreate.assert_called_once_with(
            actor_id="999",
            actor_email=None,
            action=AuditAction.CREATE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="1",
            changes={"name": "AuditDog"},
            ip_address=None,
            user_agent=None,
        )
        assert log.action == AuditAction.CREATE
        assert log.target_model == "apps_animals_app_v1.animal"
        assert log.target_object_id == "1"
        assert log.changes == {"name": "AuditDog"}

    @patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock)
    async def test_log_update_helper(self, mock_acreate):
        """Test log_update helper with mock."""
        animal = Animal(name="AuditCat", species="Cat", age=2)
        animal.id = 2

        mock_log = MagicMock()
        mock_log.action = AuditAction.UPDATE
        mock_log.target_model = "apps_animals_app_v1.animal"
        mock_log.changes = {"age": {"before": 2, "after": 3}}
        mock_acreate.return_value = mock_log

        log = await AuditService.log_update(instance=animal, changes={"age": {"before": 2, "after": 3}})

        mock_acreate.assert_called_once_with(
            actor_id=None,
            actor_email=None,
            action=AuditAction.UPDATE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="2",
            changes={"age": {"before": 2, "after": 3}},
            ip_address=None,
            user_agent=None,
        )
        assert log.action == AuditAction.UPDATE
        assert log.target_model == "apps_animals_app_v1.animal"
        assert log.changes["age"]["after"] == 3

    @patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock)
    async def test_log_delete_helper(self, mock_acreate):
        """Test log_delete helper with mock."""
        animal = Animal(name="AuditBird", species="Bird", age=1)
        animal.id = 3

        mock_log = MagicMock()
        mock_log.action = AuditAction.DELETE
        mock_log.target_model = "apps_animals_app_v1.animal"
        mock_acreate.return_value = mock_log

        log = await AuditService.log_delete(instance=animal)

        mock_acreate.assert_called_once_with(
            actor_id=None,
            actor_email=None,
            action=AuditAction.DELETE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="3",
            changes={},
            ip_address=None,
            user_agent=None,
        )
        assert log.action == AuditAction.DELETE
        assert log.target_model == "apps_animals_app_v1.animal"
