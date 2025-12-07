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
        self.get_normalized_context = patch("apps.audit_app.v1.patch.get_normalized_context").start()
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
        self.get_normalized_context.return_value = self.mock_ctx

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

    def test_audited_save_create(self):
        # Sync test for save()
        from apps.audit_app.v1.patch import audited_save

        class DummyModel:
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = None
            field1 = "val"

        DummyModel._meta.fields = [MagicMock(name="field1")]
        DummyModel._meta.fields[0].name = "field1"

        instance = DummyModel()
        instance.__original_save__ = MagicMock()

        # ACT
        audited_save(instance)

        # ASSERT
        instance.__original_save__.assert_called_once()
        self.mock_audit_service.log_create_sync.assert_called_once()
        call_kwargs = self.mock_audit_service.log_create_sync.call_args.kwargs
        assert call_kwargs["instance"] == instance
        assert call_kwargs["changes"] == {"field1": {"old": None, "new": "val"}}
        # Should rely on get_normalized_context for actor info

    def test_audited_save_update(self):
        from apps.audit_app.v1.patch import audited_save

        class DummyModel:
            objects = MagicMock()
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = 10
            field1 = "new"

        # Sync get
        old_instance = MagicMock()
        old_instance.field1 = "old"
        DummyModel.objects.get.return_value = old_instance

        DummyModel._meta.fields = [MagicMock(name="field1")]
        DummyModel._meta.fields[0].name = "field1"

        instance = DummyModel()
        instance.__original_save__ = MagicMock()

        # ACT
        audited_save(instance)

        # ASSERT
        instance.__original_save__.assert_called_once()
        self.mock_audit_service.log_update_sync.assert_called_once()
        call_kwargs = self.mock_audit_service.log_update_sync.call_args.kwargs
        assert call_kwargs["instance"] == instance
        assert call_kwargs["changes"] == {"field1": {"old": "old", "new": "new"}}

    def test_audited_delete(self):
        from apps.audit_app.v1.patch import audited_delete

        instance = MagicMock()
        instance.AUDIT_ENABLED = True
        instance.__original_delete__ = MagicMock()

        audited_delete(instance)

        instance.__original_delete__.assert_called_once()
        self.mock_audit_service.log_delete_sync.assert_called_once()
        assert self.mock_audit_service.log_delete_sync.call_args.kwargs["instance"] == instance

    def test_audited_save_disabled(self):
        from apps.audit_app.v1.patch import audited_save

        class DummyModel:
            AUDIT_ENABLED = False
            pk = None

        instance = DummyModel()
        instance.__original_save__ = MagicMock()

        audited_save(instance)

    def test_audited_save_update_missing_old(self):
        from apps.audit_app.v1.patch import audited_save

        class DummyModel:
            objects = MagicMock()
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = 10
            field1 = "new"

            class DoesNotExist(Exception):
                pass

        # Simulate race condition: pk exists but DB get fails
        DummyModel.objects.get.side_effect = DummyModel.DoesNotExist

        instance = DummyModel()
        instance.__original_save__ = MagicMock()

        # ACT
        audited_save(instance)

        # ASSERT
        instance.__original_save__.assert_called_once()
        # With new logic: if we can't find old object (e.g. UUID or race condition),
        # we treat it as a CREATE.
        self.mock_audit_service.log_create_sync.assert_called_once()
        self.mock_audit_service.log_update_sync.assert_not_called()

    def test_audited_save_update_no_changes(self):
        from apps.audit_app.v1.patch import audited_save

        class DummyModel:
            objects = MagicMock()
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = 10
            field1 = "same"

        # Sync get
        old_instance = MagicMock()
        old_instance.field1 = "same"
        DummyModel.objects.get.return_value = old_instance
        DummyModel._meta.fields = [MagicMock(name="field1")]
        DummyModel._meta.fields[0].name = "field1"

        instance = DummyModel()
        instance.__original_save__ = MagicMock()

        # ACT
        audited_save(instance)

        # ASSERT
        # Should be called with empty changes
        self.mock_audit_service.log_update_sync.assert_called_once()
        assert self.mock_audit_service.log_update_sync.call_args.kwargs["changes"] == {}

    def test_audited_delete_disabled(self):
        from apps.audit_app.v1.patch import audited_delete

        instance = MagicMock()
        instance.AUDIT_ENABLED = False
        instance.__original_delete__ = MagicMock()

        # ACT
        audited_delete(instance)

        # ASSERT
        instance.__original_delete__.assert_called_once()
        self.mock_audit_service.log_delete_sync.assert_not_called()

    def test_audited_update_queryset_sync(self):
        # Sync version of queryset update
        from apps.audit_app.v1.patch import audited_update

        # QuerySet mock
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True
        qs.model._meta.fields = [MagicMock(name="f1")]
        qs.model._meta.fields[0].name = "f1"

        # Explicitly set the "magic" method attribute
        mock_orig_update = MagicMock(return_value=1)
        qs.__original_update__ = mock_orig_update

        # Mock _clone().all() (sync iterator)
        obj_before = MagicMock(f1="old")
        obj_after = MagicMock(f1="new")

        # Mock clone
        qs_clone_1 = MagicMock()
        qs_clone_1.all.return_value = [obj_before]

        qs_clone_2 = MagicMock()
        qs_clone_2.all.return_value = [obj_after]

        qs._clone.side_effect = [qs_clone_1, qs_clone_2]

        # ACT
        audited_update(qs, f1="new")

        # ASSERT
        mock_orig_update.assert_called_once()
        self.mock_audit_service.log_update_sync.assert_called_once()
        call_kwargs = self.mock_audit_service.log_update_sync.call_args.kwargs
        assert call_kwargs["changes"] == {"f1": {"old": "old", "new": "new"}}

    def test_audited_delete_queryset_sync(self):
        # Sync version of queryset delete
        from apps.audit_app.v1.patch import audited_delete_queryset

        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True

        # Explicitly set the "magic" method attribute
        mock_orig_delete = MagicMock(return_value=(1, {}))
        qs.__original_delete_queryset__ = mock_orig_delete

        inst = MagicMock()
        qs_clone = MagicMock()
        qs_clone.all.return_value = [inst]
        qs._clone.return_value = qs_clone

        # ACT
        audited_delete_queryset(qs)

        # ASSERT
        mock_orig_delete.assert_called_once()
        self.mock_audit_service.log_delete_sync.assert_called_once()
        assert self.mock_audit_service.log_delete_sync.call_args.kwargs["instance"] == inst

    def test_audited_update_disabled(self):
        from apps.audit_app.v1.patch import audited_update

        qs = MagicMock()
        qs.model.AUDIT_ENABLED = False
        mock_orig_update = MagicMock(return_value=1)
        qs.__original_update__ = mock_orig_update

        audited_update(qs)

        mock_orig_update.assert_called_once()
        self.mock_audit_service.log_update_sync.assert_not_called()

    def test_audited_update_zero_count(self):
        from apps.audit_app.v1.patch import audited_update

        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True
        mock_orig_update = MagicMock(return_value=0)
        qs.__original_update__ = mock_orig_update

        # Act
        audited_update(qs)

        # Assert
        mock_orig_update.assert_called_once()
        # Should return early
        self.mock_audit_service.log_update_sync.assert_not_called()

    def test_audited_delete_queryset_disabled(self):
        from apps.audit_app.v1.patch import audited_delete_queryset

        qs = MagicMock()
        qs.model.AUDIT_ENABLED = False
        mock_orig_delete = MagicMock(return_value=(1, {}))
        qs.__original_delete_queryset__ = mock_orig_delete

        audited_delete_queryset(qs)

        mock_orig_delete.assert_called_once()
        self.mock_audit_service.log_delete_sync.assert_not_called()

    def test_audited_delete_queryset_zero_count(self):
        from apps.audit_app.v1.patch import audited_delete_queryset

        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True
        mock_orig_delete = MagicMock(return_value=(0, {}))
        qs.__original_delete_queryset__ = mock_orig_delete

        # We need clone to iterate (before snapshot)
        # Assuming implementation clones first.
        qs_clone = MagicMock()
        qs_clone.all.return_value = []
        qs._clone.return_value = qs_clone

        audited_delete_queryset(qs)

        mock_orig_delete.assert_called_once()
        self.mock_audit_service.log_delete_sync.assert_not_called()

    def test_audited_update_queryset_no_changes(self):
        # Sync version: values didn't change (False case of if old_val != new_val)
        from apps.audit_app.v1.patch import audited_update

        # QuerySet mock
        qs = MagicMock()
        qs.model.AUDIT_ENABLED = True
        qs.model._meta.fields = [MagicMock(name="f1")]
        qs.model._meta.fields[0].name = "f1"

        # Explicitly set the "magic" method attribute
        mock_orig_update = MagicMock(return_value=1)
        qs.__original_update__ = mock_orig_update

        # Mock _clone().all() (sync iterator)
        obj_before = MagicMock(f1="same")
        obj_after = MagicMock(f1="same")

        qs_clone_1 = MagicMock()
        qs_clone_1.all.return_value = [obj_before]

        qs_clone_2 = MagicMock()
        qs_clone_2.all.return_value = [obj_after]

        qs._clone.side_effect = [qs_clone_1, qs_clone_2]

        # ACT
        audited_update(qs, f1="same")

        # ASSERT
        mock_orig_update.assert_called_once()
        self.mock_audit_service.log_update_sync.assert_called_once()
        call_kwargs = self.mock_audit_service.log_update_sync.call_args.kwargs
        assert call_kwargs["changes"] == {}

    def test_audited_save_create_with_uuid(self):
        # Test creation where PK is already set (e.g. UUID)
        import uuid

        from apps.audit_app.v1.patch import audited_save

        class DummyModel:
            objects = MagicMock()
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = uuid.uuid4()  # PK is set!
            field1 = "val"

            class DoesNotExist(Exception):
                pass

        DummyModel._meta.fields = [MagicMock(name="field1")]
        DummyModel._meta.fields[0].name = "field1"

        # Simulate new object: PK exists in memory but NOT in DB
        DummyModel.objects.get.side_effect = DummyModel.DoesNotExist

        instance = DummyModel()
        instance.__original_save__ = MagicMock()

        # ACT
        audited_save(instance)

        # ASSERT
        instance.__original_save__.assert_called_once()
        # Should be logged as CREATE, not update (and not ignored!)
        self.mock_audit_service.log_create_sync.assert_called_once()
        call_kwargs = self.mock_audit_service.log_create_sync.call_args.kwargs
        assert call_kwargs["instance"] == instance
        assert call_kwargs["changes"] == {"field1": {"old": None, "new": "val"}}

    async def test_audited_asave_create_with_uuid(self):
        # Async version: PK is set (e.g. UUID) but object doesn't exist in DB
        import uuid

        class DummyModel:
            objects = MagicMock()
            _meta = MagicMock()
            AUDIT_ENABLED = True
            pk = uuid.uuid4()
            field1 = "val"

            class DoesNotExist(Exception):
                pass

        DummyModel._meta.fields = [MagicMock(name="field1")]
        DummyModel._meta.fields[0].name = "field1"

        # Mock objects.aget to raise DoesNotExist
        DummyModel.objects.aget = AsyncMock(side_effect=DummyModel.DoesNotExist)

        instance = DummyModel()
        instance.__original_asave__ = AsyncMock()

        # ACT
        await audited_asave(instance)

        # ASSERT
        instance.__original_asave__.assert_called_once()
        self.mock_audit_service.log_create.assert_called_once()
        call_kwargs = self.mock_audit_service.log_create.call_args.kwargs
        assert call_kwargs["changes"] == {"field1": {"old": None, "new": "val"}}
