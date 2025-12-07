from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.audit_app.v1.patcher import AuditPatcher

# ============================================================
#  SHARED MOCK HELPERS
# ============================================================


def make_instance(audit_enabled=True):
    """Creates a fake Django Model instance."""
    inst = MagicMock()
    inst.pk = "123"
    inst.AUDIT_ENABLED = audit_enabled
    inst.__class__.objects = MagicMock()
    inst.__class__.DoesNotExist = Exception
    return inst


def make_qs(model):
    """Creates a fake Django QuerySet."""
    qs = MagicMock()
    qs.model = model
    qs._clone.return_value = qs
    return qs


# ============================================================
#  ASYNC: asave()
# ============================================================


@pytest.mark.asyncio
class TestAuditPatcherASave:

    async def test_asave_create_calls_log_create(self):
        inst = make_instance(audit_enabled=True)
        inst.pk = None  # New object
        inst.__original_asave__ = AsyncMock(return_value="saved")

        with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"x": 1}):
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()
            ) as mocked:
                result = await AuditPatcher.asave(inst)

        mocked.assert_awaited_once_with(inst, {"x": 1})
        assert result == "saved"

    async def test_asave_update_calls_log_update(self):
        inst = make_instance(audit_enabled=True)
        old_obj = MagicMock()
        inst.__original_asave__ = AsyncMock(return_value="saved")

        inst.__class__.objects.aget = AsyncMock(return_value=old_obj)

        with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"x": 2}):
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_update_async", new=AsyncMock()
            ) as mocked:
                await AuditPatcher.asave(inst)

        mocked.assert_awaited_once_with(inst, {"x": 2})

    async def test_asave_respects_audit_disabled(self):
        inst = make_instance(audit_enabled=False)
        inst.__original_asave__ = AsyncMock(return_value="saved")

        with patch(
            "apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()
        ) as mocked_create:
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_update_async", new=AsyncMock()
            ) as mocked_update:
                await AuditPatcher.asave(inst)

        mocked_create.assert_not_called()
        mocked_update.assert_not_called()


# ============================================================
#  ASYNC: adelete()
# ============================================================


@pytest.mark.asyncio
class TestAuditPatcherADelete:

    async def test_adelete_calls_log_delete(self):
        inst = make_instance(audit_enabled=True)
        inst.__original_adelete__ = AsyncMock(return_value="deleted")

        with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"y": 9}):
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()
            ) as mocked:
                result = await AuditPatcher.adelete(inst)

        mocked.assert_awaited_once_with(inst, {"y": 9})
        assert result == "deleted"

    async def test_adelete_skips_when_audit_disabled(self):
        inst = make_instance(audit_enabled=False)
        inst.__original_adelete__ = AsyncMock()

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()) as mocked:
            await AuditPatcher.adelete(inst)

        mocked.assert_not_called()


# ============================================================
#  ASYNC: acreate()
# ============================================================


@pytest.mark.asyncio
class TestAuditPatcherACreate:

    async def test_acreate_calls_log_create(self):
        fake_model = MagicMock(AUDIT_ENABLED=True)
        manager = MagicMock(model=fake_model)
        fake_instance = MagicMock()

        manager.__original_acreate__ = AsyncMock(return_value=fake_instance)

        with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"z": 5}):
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()
            ) as mocked:
                result = await AuditPatcher.acreate(manager, name="Tiger")

        mocked.assert_awaited_once_with(fake_instance, {"z": 5})
        assert result == fake_instance

    async def test_acreate_skips_when_audit_disabled(self):
        fake_model = MagicMock(AUDIT_ENABLED=False)
        manager = MagicMock(model=fake_model)
        fake_instance = MagicMock()
        manager.__original_acreate__ = AsyncMock(return_value=fake_instance)

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()) as mocked:
            await AuditPatcher.acreate(manager)

        mocked.assert_not_called()


# ============================================================
#  ASYNC: aupdate()
# ============================================================


@pytest.mark.asyncio
class TestAuditPatcherAUpdate:

    async def test_aupdate_calls_log_update(self):
        fake_model = MagicMock(AUDIT_ENABLED=True)
        qs = make_qs(fake_model)
        old_obj = MagicMock()
        new_obj = MagicMock()

        qs.__original_aupdate__ = AsyncMock(return_value=1)

        # before + after snapshots
        async def async_before():
            yield old_obj

        async def async_after():
            yield new_obj

        qs._clone.side_effect = [qs, qs]
        qs.all.return_value = qs
        qs.__aiter__ = lambda *_: async_before()
        qs.__aiter__ = lambda *_: async_after()

        with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"a": 99}):
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_update_async", new=AsyncMock()
            ) as mocked:
                await AuditPatcher.aupdate(qs)

        mocked.assert_awaited_once_with(new_obj, {"a": 99})

    async def test_aupdate_skips_when_audit_disabled(self):
        fake_model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(fake_model)
        qs.__original_aupdate__ = AsyncMock(return_value=1)

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_async", new=AsyncMock()) as mocked:
            await AuditPatcher.aupdate(qs)

        mocked.assert_not_called()


# ============================================================
#  ASYNC: adelete_queryset()
# ============================================================


@pytest.mark.asyncio
class TestAuditPatcherADeleteQueryset:

    async def test_adelete_queryset_calls_log_delete(self):
        fake_model = MagicMock(AUDIT_ENABLED=True)
        qs = make_qs(fake_model)
        obj = MagicMock()

        qs.__original_adelete_queryset__ = AsyncMock(return_value=(1, {}))

        async def async_iter():
            yield obj

        qs._clone.return_value = qs
        qs.all.return_value = qs
        qs.__aiter__ = lambda *_: async_iter()

        with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"gone": True}):
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()
            ) as mocked:
                await AuditPatcher.adelete_queryset(qs)

        mocked.assert_awaited_once_with(obj, {"gone": True})

    async def test_adelete_queryset_skips_when_audit_disabled(self):
        fake_model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(fake_model)
        qs.__original_adelete_queryset__ = AsyncMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()) as mocked:
            await AuditPatcher.adelete_queryset(qs)

        mocked.assert_not_called()


# ============================================================
#  SYNC PATCHES
# ============================================================


class TestAuditPatcherSyncSave:

    def test_sync_save_create(self):
        inst = make_instance(audit_enabled=True)
        inst.pk = None  # New object
        inst.__original_save__ = MagicMock(return_value="saved")

        with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"x": 1}):
            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync") as mocked:
                result = AuditPatcher.save(inst)

        mocked.assert_called_once_with(inst, {"x": 1})
        assert result == "saved"

    def test_sync_save_update(self):
        inst = make_instance(audit_enabled=True)
        old_obj = MagicMock()

        inst.__original_save__ = MagicMock(return_value="saved")
        inst.__class__.objects.get = MagicMock(return_value=old_obj)

        with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"u": 44}):
            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync") as mocked:
                AuditPatcher.save(inst)

        mocked.assert_called_once_with(inst, {"u": 44})

    def test_sync_save_skips_when_disabled(self):
        inst = make_instance(audit_enabled=False)
        inst.__original_save__ = MagicMock()

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync") as mocked:
            AuditPatcher.save(inst)

        mocked.assert_not_called()


class TestAuditPatcherSyncDelete:

    def test_sync_delete(self):
        inst = make_instance(True)
        inst.__original_delete__ = MagicMock(return_value="deleted")

        with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"gone": 1}):
            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mocked:
                AuditPatcher.delete(inst)

        mocked.assert_called_once_with(inst, {"gone": 1})

    def test_sync_delete_skips_when_disabled(self):
        inst = make_instance(False)
        inst.__original_delete__ = MagicMock()

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mocked:
            AuditPatcher.delete(inst)

        mocked.assert_not_called()


class TestAuditPatcherSyncUpdate:

    def test_sync_update(self):
        model = MagicMock(AUDIT_ENABLED=True)
        qs = make_qs(model)

        old_obj = MagicMock()
        new_obj = MagicMock()
        qs._clone().all.return_value = [old_obj]
        qs.__original_update__ = MagicMock(return_value=1)

        qs._clone.side_effect = [qs, qs]  # before, after
        qs._clone().all.side_effect = [[old_obj], [new_obj]]

        with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"k": 7}):
            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync") as mocked:
                AuditPatcher.update(qs)

        mocked.assert_called_once_with(new_obj, {"k": 7})

    def test_sync_update_skips_when_disabled(self):
        model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(model)
        qs.__original_update__ = MagicMock(return_value=1)

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync") as mocked:
            AuditPatcher.update(qs)

        mocked.assert_not_called()


class TestAuditPatcherSyncDeleteQueryset:

    def test_sync_delete_queryset(self):
        model = MagicMock(AUDIT_ENABLED=True)
        qs = make_qs(model)
        inst = MagicMock()

        qs._clone().all.return_value = [inst]
        qs.__original_delete_queryset__ = MagicMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"gone": True}):
            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mocked:
                AuditPatcher.delete_queryset(qs)

        mocked.assert_called_once_with(inst, {"gone": True})

    def test_sync_delete_queryset_skips_when_disabled(self):
        model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(model)
        qs.__original_delete_queryset__ = MagicMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mocked:
            AuditPatcher.delete_queryset(qs)

        mocked.assert_not_called()
