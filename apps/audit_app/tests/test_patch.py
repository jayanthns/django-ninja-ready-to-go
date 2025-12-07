from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.audit_app.v1.patch import (
    audited_acreate,
    audited_adelete,
    audited_adelete_queryset,
    audited_asave,
    audited_aupdate,
)

# Common context every audit function expects
FULL_CONTEXT = {
    "actor_id": "1",
    "actor_email": "a@a.com",
    "trace_id": "t1",
    "correlation_id": "c1",
    "session_key": "s1",
    "ip_address": "127.0.0.1",
    "user_agent": "agent",
}


# ------------------------------------------------------------------------------
# ASAVE
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
class TestAuditedASave:

    async def test_asave_create_calls_log_create(self):
        instance = MagicMock()
        instance.pk = None
        instance.AUDIT_ENABLED = True
        instance._meta.fields = []
        instance.__original_asave__ = AsyncMock(return_value="saved")

        with patch("apps.audit_app.v1.patch.get_context", return_value=FULL_CONTEXT):
            with patch("apps.audit_app.v1.patch.AuditService.log_create", new=AsyncMock()) as mocked:

                result = await audited_asave(instance)

                assert result == "saved"
                mocked.assert_called_once()

    async def test_asave_update_calls_log_update(self):
        # Fake model + objects manager with aget()
        class FakeModel:
            objects = MagicMock()

        instance = MagicMock()
        instance.__class__ = FakeModel  # give instance a class with objects
        instance.pk = 1
        instance.AUDIT_ENABLED = True
        instance._meta.fields = []
        instance.__original_asave__ = AsyncMock(return_value="saved")

        FakeModel.objects.aget = AsyncMock(return_value=MagicMock())

        with patch("apps.audit_app.v1.patch.get_context", return_value=FULL_CONTEXT):
            with patch("apps.audit_app.v1.patch.AuditService.log_update", new=AsyncMock()) as mocked:

                await audited_asave(instance)
                mocked.assert_called_once()


# ------------------------------------------------------------------------------
# ADELETE
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
class TestAuditedADelete:

    async def test_adelete_calls_log_delete(self):
        instance = MagicMock()
        instance.AUDIT_ENABLED = True
        instance.__original_adelete__ = AsyncMock(return_value="deleted")

        with patch("apps.audit_app.v1.patch.get_context", return_value=FULL_CONTEXT):
            with patch("apps.audit_app.v1.patch.AuditService.log_delete", new=AsyncMock()) as mocked:

                result = await audited_adelete(instance)
                assert result == "deleted"
                mocked.assert_called_once()


# ------------------------------------------------------------------------------
# ACREATE
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
class TestAuditedACreate:

    async def test_acreate_calls_log_create(self):
        fake_model = MagicMock()
        fake_model.AUDIT_ENABLED = True
        fake_model._meta.fields = []

        fake_instance = MagicMock()
        fake_instance._meta.fields = []

        manager = MagicMock(model=fake_model)
        manager.__original_acreate__ = AsyncMock(return_value=fake_instance)

        with patch("apps.audit_app.v1.patch.get_context", return_value=FULL_CONTEXT):
            with patch("apps.audit_app.v1.patch.AuditService.log_create", new=AsyncMock()) as mocked:

                result = await audited_acreate(manager, name="Tiger")
                assert result == fake_instance
                mocked.assert_called_once()


# ------------------------------------------------------------------------------
# AUPDATE
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
class TestAuditedAUpdate:

    async def test_aupdate_calls_log_update(self):
        fake_model = MagicMock()
        fake_model.AUDIT_ENABLED = True
        fake_model._meta.fields = []

        qs = MagicMock()
        qs.model = fake_model

        qs.__original_aupdate__ = AsyncMock(return_value=1)

        # Before & after values
        qs._clone.return_value = qs
        qs.all.return_value = qs

        async def async_iter_before():
            yield MagicMock()

        async def async_iter_after():
            yield MagicMock()

        qs.__aiter__ = lambda _: async_iter_before()

        with patch("apps.audit_app.v1.patch.get_context", return_value=FULL_CONTEXT):
            with patch("apps.audit_app.v1.patch.AuditService.log_update", new=AsyncMock()) as mocked:

                qs._clone.side_effect = [qs, qs]  # before and after snapshots

                await audited_aupdate(qs, name="Lion")
                mocked.assert_called_once()


# ------------------------------------------------------------------------------
# ADELETE QUERYSET
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
class TestAuditedADeleteQueryset:

    async def test_adelete_queryset_calls_log_delete(self):
        fake_model = MagicMock()
        fake_model.AUDIT_ENABLED = True

        qs = MagicMock()
        qs.model = fake_model
        qs._clone.return_value = qs
        qs.all.return_value = qs

        async def async_iter():
            yield MagicMock()

        qs.__aiter__ = lambda _: async_iter()

        qs.__original_adelete_queryset__ = AsyncMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patch.get_context", return_value=FULL_CONTEXT):
            with patch("apps.audit_app.v1.patch.AuditService.log_delete", new=AsyncMock()) as mocked:

                count, details = await audited_adelete_queryset(qs)
                assert count == 1
                mocked.assert_called_once()
