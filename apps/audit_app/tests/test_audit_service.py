from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.animals_app.v1.models import Animal
from apps.audit_app.v1.services import AuditService
from common.enums import AuditAction


@pytest.mark.asyncio
class TestAuditService:
    @patch("apps.audit_app.v1.services.normalize_value")
    @patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock)
    async def test_log_event_generic(self, mock_acreate, mock_normalize):
        """Test generic event logging with mock."""
        mock_normalize.side_effect = lambda x: x
        mock_log = MagicMock()
        mock_log.action = AuditAction.LOGIN
        mock_log.ip_address = "127.0.0.1"
        mock_log.actor_id = "123"
        mock_log.actor_email = "test@example.com"
        mock_log.trace_id = "trace_id"
        mock_log.correlation_id = "correlation_id"
        mock_log.session_key = "session_key"
        mock_acreate.return_value = mock_log

        await AuditService.log_event(
            action=AuditAction.LOGIN,
            target_model="auth.User",
            target_object_id="1",
            ip_address="127.0.0.1",
            actor_id="123",
            actor_email="test@example.com",
            trace_id="trace_id",
            correlation_id="correlation_id",
            session_key="session_key",
        )

        # normalize_value is called for each field
        assert mock_normalize.call_count >= 1

        mock_acreate.assert_called_once_with(
            action=AuditAction.LOGIN,
            target_model="auth.User",
            target_object_id="1",
            trace_id="trace_id",
            changes={},
            actor_id="123",
            actor_email="test@example.com",
            correlation_id="correlation_id",
            session_key="session_key",
            object_representation=None,
            ip_address="127.0.0.1",
            user_agent=None,
        )

    @patch("apps.audit_app.v1.services.normalize_value")
    @patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock)
    async def test_log_create_helper(self, mock_acreate, mock_normalize):
        mock_normalize.side_effect = lambda x: x
        animal = Animal(name="AuditDog", species="Dog", age=3)
        animal.id = 1

        mock_log = MagicMock()
        mock_acreate.return_value = mock_log

        await AuditService.log_create(
            instance=animal,
            actor_id="999",
            changes={"name": {"old": None, "new": "AuditDog"}},
            trace_id="trace_id",
            correlation_id="correlation_id",
            session_key="session_key",
            object_representation="AuditDog",
        )

        mock_acreate.assert_called_once_with(
            action=AuditAction.CREATE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="1",
            trace_id="trace_id",
            changes={"name": {"old": None, "new": "AuditDog"}},
            actor_id="999",
            actor_email=None,
            correlation_id="correlation_id",
            session_key="session_key",
            object_representation="AuditDog",
            ip_address=None,
            user_agent=None,
        )

    @patch("apps.audit_app.v1.services.normalize_value")
    @patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock)
    async def test_log_update_helper(self, mock_acreate, mock_normalize):
        mock_normalize.side_effect = lambda x: x
        animal = Animal(name="AuditCat", species="Cat", age=2)
        animal.id = 2

        mock_log = MagicMock()
        mock_acreate.return_value = mock_log

        await AuditService.log_update(
            instance=animal,
            changes={"age": {"old": 2, "new": 3}},
            trace_id="trace_id",
            correlation_id="correlation_id",
            session_key="session_key",
        )

        mock_acreate.assert_called_once_with(
            action=AuditAction.UPDATE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="2",
            trace_id="trace_id",
            changes={"age": {"old": 2, "new": 3}},
            actor_id=None,
            actor_email=None,
            correlation_id="correlation_id",
            session_key="session_key",
            object_representation=None,
            ip_address=None,
            user_agent=None,
        )

    @patch("apps.audit_app.v1.services.normalize_value")
    @patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock)
    async def test_log_delete_helper(self, mock_acreate, mock_normalize):
        mock_normalize.side_effect = lambda x: x
        animal = Animal(name="AuditBird", species="Bird", age=1)
        animal.id = 3

        mock_log = MagicMock()
        mock_acreate.return_value = mock_log

        await AuditService.log_delete(
            instance=animal,
            trace_id="trace_id",
            correlation_id="correlation_id",
            session_key="session_key",
        )

        mock_acreate.assert_called_once_with(
            action=AuditAction.DELETE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="3",
            trace_id="trace_id",
            changes={},
            actor_id=None,
            actor_email=None,
            correlation_id="correlation_id",
            session_key="session_key",
            object_representation=None,
            ip_address=None,
            user_agent=None,
        )

    @patch("apps.audit_app.v1.services.normalize_value")
    @patch("apps.audit_app.v1.services.AuditLog.objects.create")
    def test_log_create_sync(self, mock_create, mock_normalize):
        mock_normalize.side_effect = lambda x: x
        animal = Animal(name="SyncDog", species="Dog", age=4)
        animal.id = 4
        mock_create.return_value = MagicMock()

        AuditService.log_create_sync(
            instance=animal,
            actor_id="101",
            changes={"name": {"old": None, "new": "SyncDog"}},
            trace_id="trace_id",
            object_representation="SyncDog",
        )

        mock_create.assert_called_once_with(
            action=AuditAction.CREATE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="4",
            trace_id="trace_id",
            changes={"name": {"old": None, "new": "SyncDog"}},
            actor_id="101",
            actor_email=None,
            correlation_id=None,
            session_key=None,
            object_representation="SyncDog",
            ip_address=None,
            user_agent=None,
        )

    @patch("apps.audit_app.v1.services.normalize_value")
    @patch("apps.audit_app.v1.services.AuditLog.objects.create")
    def test_log_update_sync(self, mock_create, mock_normalize):
        mock_normalize.side_effect = lambda x: x
        animal = Animal(name="SyncCat", species="Cat", age=5)
        animal.id = 5
        mock_create.return_value = MagicMock()

        AuditService.log_update_sync(
            instance=animal,
            changes={"age": {"old": 5, "new": 6}},
            trace_id="trace_id",
            object_representation="SyncCat",
        )

        mock_create.assert_called_once_with(
            action=AuditAction.UPDATE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="5",
            trace_id="trace_id",
            changes={"age": {"old": 5, "new": 6}},
            actor_id=None,
            actor_email=None,
            correlation_id=None,
            session_key=None,
            object_representation="SyncCat",
            ip_address=None,
            user_agent=None,
        )

    @patch("apps.audit_app.v1.services.normalize_value")
    @patch("apps.audit_app.v1.services.AuditLog.objects.create")
    def test_log_delete_sync(self, mock_create, mock_normalize):
        mock_normalize.side_effect = lambda x: x
        animal = Animal(name="SyncBird", species="Bird", age=6)
        animal.id = 6
        mock_create.return_value = MagicMock()

        AuditService.log_delete_sync(
            instance=animal,
            trace_id="trace_id",
            object_representation="SyncBird",
        )

        mock_create.assert_called_once_with(
            action=AuditAction.DELETE,
            target_model="apps_animals_app_v1.animal",
            target_object_id="6",
            trace_id="trace_id",
            changes={},
            actor_id=None,
            actor_email=None,
            correlation_id=None,
            session_key=None,
            object_representation="SyncBird",
            ip_address=None,
            user_agent=None,
        )
