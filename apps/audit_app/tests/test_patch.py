from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.audit_app.v1.patch import (
    audited_acreate,
    audited_adelete,
    audited_adelete_queryset,
    audited_asave,
    audited_aupdate,
)


@pytest.mark.asyncio
class TestPatch:

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.mock_get_context = patch("apps.audit_app.v1.patch.get_context").start()
        self.mock_audit_service = patch("apps.audit_app.v1.patch.AuditService").start()

        self.mock_ctx = {
            "actor_id": "user-1",
            "actor_email": "user@example.com",
            "trace_id": "trace-1",
            "correlation_id": "corr-1",
            "session_key": "sess-1",
            "ip_address": "127.0.0.1",
            "user_agent": "TestAgent",
        }
        self.mock_get_context.return_value = self.mock_ctx

        # Configure AuditService async mocks
        self.mock_audit_service.log_create = AsyncMock()
        self.mock_audit_service.log_update = AsyncMock()
        self.mock_audit_service.log_delete = AsyncMock()

        yield

        patch.stopall()

    async def test_audited_asave_create(self):
        # Use a dummy class to avoid MagicMock __class__ issues if they arise,
        # though explicitly mocking _meta is key here.
        class DummyModel:
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = None
            field1 = "value1"
            field2 = "value2"

        DummyModel._meta.fields = [MagicMock(name="field1"), MagicMock(name="field2")]
        DummyModel._meta.fields[0].name = "field1"
        DummyModel._meta.fields[1].name = "field2"

        instance = DummyModel()
        instance.__original_asave__ = AsyncMock()

        # ACT
        await audited_asave(instance)

        # ASSERT
        instance.__original_asave__.assert_called_once()
        self.mock_audit_service.log_create.assert_called_once()
        call_kwargs = self.mock_audit_service.log_create.call_args.kwargs
        assert call_kwargs["instance"] == instance
        assert call_kwargs["changes"] == {
            "field1": {"old": None, "new": "value1"},
            "field2": {"old": None, "new": "value2"},
        }
        assert call_kwargs["actor_id"] == "user-1"

    async def test_audited_asave_update(self):
        # Create a dummy class to mock __class__.objects interaction
        class DummyModel:
            objects = MagicMock()
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = 1
            field1 = "new_value"

        DummyModel.objects.aget = AsyncMock()
        old_instance = MagicMock()
        old_instance.field1 = "old_value"
        DummyModel.objects.aget.return_value = old_instance

        DummyModel._meta.fields = [MagicMock(name="field1")]
        DummyModel._meta.fields[0].name = "field1"

        instance = DummyModel()
        instance.__original_asave__ = AsyncMock()

        # ACT
        await audited_asave(instance)

        # ASSERT
        instance.__original_asave__.assert_called_once()
        self.mock_audit_service.log_update.assert_called_once()
        call_kwargs = self.mock_audit_service.log_update.call_args.kwargs
        assert call_kwargs["instance"] == instance
        assert call_kwargs["changes"] == {"field1": {"old": "old_value", "new": "new_value"}}

    async def test_audited_asave_disabled(self):
        class DummyModel:
            objects = MagicMock()
            AUDIT_ENABLED = False
            pk = 1

        DummyModel.objects.aget = AsyncMock()
        instance = DummyModel()
        instance.__original_asave__ = AsyncMock()

        await audited_asave(instance)

        instance.__original_asave__.assert_called_once()
        self.mock_audit_service.log_create.assert_not_called()
        self.mock_audit_service.log_update.assert_not_called()

    async def test_audited_adelete(self):
        instance = MagicMock()
        instance.AUDIT_ENABLED = True
        instance.__original_adelete__ = AsyncMock()

        await audited_adelete(instance)

        instance.__original_adelete__.assert_called_once()
        self.mock_audit_service.log_delete.assert_called_once()
        assert self.mock_audit_service.log_delete.call_args.kwargs["instance"] == instance

    async def test_audited_acreate(self):
        # Manager mock
        manager = MagicMock()
        manager.model.AUDIT_ENABLED = True
        manager.model._meta.fields = [MagicMock(name="f1")]
        manager.model._meta.fields[0].name = "f1"

        created_instance = MagicMock()
        created_instance.f1 = "val1"

        manager.__original_acreate__ = AsyncMock(return_value=created_instance)

        # ACT
        await audited_acreate(manager, f1="val1")

        # ASSERT
        manager.__original_acreate__.assert_called_once()
        self.mock_audit_service.log_create.assert_called_once()
        assert self.mock_audit_service.log_create.call_args.kwargs["instance"] == created_instance

    async def test_audited_aupdate(self):
        # QuerySet mock
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True
        qs.model._meta.fields = [MagicMock(name="f1")]
        qs.model._meta.fields[0].name = "f1"

        # Mock __original_aupdate__
        qs.__original_aupdate__ = AsyncMock(return_value=1)

        # Mock _clone().all() (async iterator)
        obj_before = MagicMock(f1="old")
        obj_after = MagicMock(f1="new")

        async def async_iter(items):
            for i in items:
                yield i

        # Mock clone
        qs_clone_1 = MagicMock()
        qs_clone_1.all.return_value = async_iter([obj_before])

        qs_clone_2 = MagicMock()
        qs_clone_2.all.return_value = async_iter([obj_after])

        qs._clone.side_effect = [qs_clone_1, qs_clone_2]

        # ACT
        await audited_aupdate(qs, f1="new")

        # ASSERT
        qs.__original_aupdate__.assert_called_once()
        self.mock_audit_service.log_update.assert_called_once()
        call_kwargs = self.mock_audit_service.log_update.call_args.kwargs
        assert call_kwargs["changes"] == {"f1": {"old": "old", "new": "new"}}

    async def test_audited_adelete_queryset(self):
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True

        qs.__original_adelete_queryset__ = AsyncMock(return_value=(1, {}))

        obj = MagicMock()

        async def async_iter(items):
            for i in items:
                yield i

        qs_clone = MagicMock()
        qs_clone.all.return_value = async_iter([obj])
        qs._clone.return_value = qs_clone

        # ACT
        await audited_adelete_queryset(qs)

        # ASSERT
        self.mock_audit_service.log_delete.assert_called_once()
        assert self.mock_audit_service.log_delete.call_args.kwargs["instance"] == obj

    async def test_audited_adelete_disabled(self):
        instance = MagicMock()
        instance.AUDIT_ENABLED = False
        instance.__original_adelete__ = AsyncMock()

        await audited_adelete(instance)

        instance.__original_adelete__.assert_called_once()
        self.mock_audit_service.log_delete.assert_not_called()

    async def test_audited_acreate_disabled(self):
        manager = MagicMock()
        manager.model.AUDIT_ENABLED = False
        manager.__original_acreate__ = AsyncMock()

        await audited_acreate(manager)

        manager.__original_acreate__.assert_called_once()
        self.mock_audit_service.log_create.assert_not_called()

    async def test_audited_aupdate_disabled(self):
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = False
        qs.__original_aupdate__ = AsyncMock()

        await audited_aupdate(qs)

        qs.__original_aupdate__.assert_called_once()
        self.mock_audit_service.log_update.assert_not_called()

    async def test_audited_aupdate_zero_impact(self):
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True

        # Return 0 updated rows
        qs.__original_aupdate__ = AsyncMock(return_value=0)

        async def async_iter(items):
            for i in items:
                yield i

        qs_clone = MagicMock()
        qs_clone.all.return_value = async_iter([])
        qs._clone.return_value = qs_clone

        await audited_aupdate(qs)

        qs.__original_aupdate__.assert_called_once()
        self.mock_audit_service.log_update.assert_not_called()

    async def test_audited_asave_no_change(self):
        # Case where old_val == new_val (line 46)
        class DummyModel:
            objects = MagicMock()
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = 1
            field1 = "same_value"

        DummyModel.objects.aget = AsyncMock()
        old_instance = MagicMock()
        old_instance.field1 = "same_value"
        DummyModel.objects.aget.return_value = old_instance

        DummyModel._meta.fields = [MagicMock(name="field1")]
        DummyModel._meta.fields[0].name = "field1"

        instance = DummyModel()
        instance.__original_asave__ = AsyncMock()

        await audited_asave(instance)

        # log_update is called but with empty changes? The code allows empty changes currently.
        # Let's check the changes dict passed.
        self.mock_audit_service.log_update.assert_called_once()
        call_kwargs = self.mock_audit_service.log_update.call_args.kwargs
        assert call_kwargs["changes"] == {}

    async def test_audited_adelete_queryset_disabled(self):
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = False
        qs.__original_adelete_queryset__ = AsyncMock()

        await audited_adelete_queryset(qs)

        qs.__original_adelete_queryset__.assert_called_once()
        self.mock_audit_service.log_delete.assert_not_called()

    async def test_audited_adelete_queryset_zero_impact(self):
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True

        # Return 0 deleted rows
        qs.__original_adelete_queryset__ = AsyncMock(return_value=(0, {}))

        async def async_iter(items):
            for i in items:
                yield i

        # Before snapshot might happen, but execution stops after adelete returns 0
        qs_clone = MagicMock()
        qs_clone.all.return_value = async_iter([])
        qs._clone.return_value = qs_clone

        await audited_adelete_queryset(qs)

        qs.__original_adelete_queryset__.assert_called_once()
        self.mock_audit_service.log_delete.assert_not_called()

    async def test_audited_aupdate_no_change(self):
        # QuerySet mock
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True
        qs.model._meta.fields = [MagicMock(name="f1")]
        qs.model._meta.fields[0].name = "f1"

        # Mock __original_aupdate__
        qs.__original_aupdate__ = AsyncMock(return_value=1)

        # Mock _clone().all() (async iterator)
        obj_before = MagicMock(f1="same")
        obj_after = MagicMock(f1="same")

        async def async_iter(items):
            for i in items:
                yield i

        # Mock clone
        qs_clone_1 = MagicMock()
        qs_clone_1.all.return_value = async_iter([obj_before])

        qs_clone_2 = MagicMock()
        qs_clone_2.all.return_value = async_iter([obj_after])

        qs._clone.side_effect = [qs_clone_1, qs_clone_2]

        # ACT
        await audited_aupdate(qs, f1="same")

        # ASSERT
        qs.__original_aupdate__.assert_called_once()

        # Should still log update, but with empty changes
        self.mock_audit_service.log_update.assert_called_once()
        call_kwargs = self.mock_audit_service.log_update.call_args.kwargs
        assert call_kwargs["changes"] == {}
