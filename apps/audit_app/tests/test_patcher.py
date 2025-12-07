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
    inst._audit_in_progress = False  # Important: prevent recursion check from returning Mock (truthy)
    inst.__class__.objects = MagicMock()
    inst.__class__.DoesNotExist = Exception
    # Also set for class if accessed via class
    inst.model = MagicMock()
    inst.model.AUDIT_ENABLED = audit_enabled
    return inst


# ... (skipping unchanged parts)


class TestAuditPatcherInternals:

    @pytest.mark.asyncio
    async def test_audit_create_async_internals(self):
        with patch(
            "apps.audit_app.v1.patcher.get_normalized_context", return_value={"user": "test"}
        ) as mock_ctx:
            with patch(
                "apps.audit_app.v1.patcher.TaskDispatcher.dispatch_create", new=AsyncMock()
            ) as mock_dispatch:
                inst = MagicMock()
                inst._meta.app_label = "app"
                inst._meta.model_name = "model"
                inst.pk = "1"
                changes = {"a": 1}
                await AuditPatcher.audit_create_async(inst, changes)

                mock_ctx.assert_called_once()
                mock_dispatch.assert_awaited_once()
                args, kwargs = mock_dispatch.call_args
                assert kwargs["payload"]["changes"] == changes

    @pytest.mark.asyncio
    async def test_audit_update_async_internals(self):
        with patch(
            "apps.audit_app.v1.patcher.get_normalized_context", return_value={"user": "test1"}
        ) as mock_ctx:
            with patch(
                "apps.audit_app.v1.patcher.TaskDispatcher.dispatch_update", new=AsyncMock()
            ) as mock_dispatch:
                inst = MagicMock()
                inst._meta.app_label = "app"
                inst._meta.model_name = "model"
                inst.pk = "2"
                changes = {"b": 2}
                await AuditPatcher.audit_update_async(inst, changes)

                mock_ctx.assert_called_once()
                mock_dispatch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_audit_delete_async_internals(self):
        with patch(
            "apps.audit_app.v1.patcher.get_normalized_context", return_value={"user": "test2"}
        ) as mock_ctx:
            with patch(
                "apps.audit_app.v1.patcher.TaskDispatcher.dispatch_delete", new=AsyncMock()
            ) as mock_dispatch:
                inst = MagicMock()
                inst._meta.app_label = "app"
                inst._meta.model_name = "model"
                inst.pk = "3"
                changes = {"c": 3}
                await AuditPatcher.audit_delete_async(inst, changes)

                mock_ctx.assert_called_once()
                mock_dispatch.assert_awaited_once()

    def test_audit_create_sync_internals(self):
        with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={"user": "test3"}):
            with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_create") as mock_dispatch:
                # async_to_sync wrapper returns a callable, which calls dispatch_create
                # Wait, async_to_sync(func)(args). Mocking dispatch_create might be tricky if async_to_sync wraps it.
                # However, usually async_to_sync works on coroutines.
                # Actually, patcher uses async_to_sync(TaskDispatcher.dispatch_create)(payload=payload)

                # We need to mock async_to_sync to just call the function or return a wrapper?
                # Or just mock dispatch_create if async_to_sync executes it.
                # async_to_sync expects an awaitable. AsyncMock is awaitable.

                # Let's mock async_to_sync to execute immediately for sync tests
                with patch("apps.audit_app.v1.patcher.async_to_sync", side_effect=lambda f: f):
                    # But dispatch_create is async. Lambda returns it. Calling it returns coroutine.
                    # We need side_effect to return a function that 'awaits' it? No, sync test.

                    # Better: mock TaskDispatcher.dispatch_create as a regular Mock,
                    # AND mock async_to_sync to return a function that calls the inner function?
                    # Since dispatch_create is async, calling it returns a coroutine.
                    # We probably want to check if dispatch_create was called.

                    mock_dispatch = MagicMock()
                    with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_create", mock_dispatch):
                        inst = MagicMock()
                        inst._meta.app_label = "app"
                        inst._meta.model_name = "model"
                        inst.pk = "4"
                        changes = {"a": 1}

                        AuditPatcher.audit_create_sync(inst, changes)

                        # Since we mocked async_to_sync to (lambda f: f),
                        # it executes dispatch_create(payload=payload).
                        # So mock_dispatch should be called.
                        mock_dispatch.assert_called_once()

    def test_audit_update_sync_internals(self):
        with patch("apps.audit_app.v1.patcher.async_to_sync", side_effect=lambda f: f):
            with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_update") as mock_dispatch:
                inst = MagicMock()
                inst._meta.app_label = "app"
                inst._meta.model_name = "model"
                inst.pk = "5"
                changes = {"b": 2}
                AuditPatcher.audit_update_sync(inst, changes)

                mock_dispatch.assert_called_once()

    def test_audit_delete_sync_internals(self):
        with patch("apps.audit_app.v1.patcher.async_to_sync", side_effect=lambda f: f):
            with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_delete") as mock_dispatch:
                inst = MagicMock()
                inst._meta.app_label = "app"
                inst._meta.model_name = "model"
                inst.pk = "6"
                changes = {"c": 3}
                AuditPatcher.audit_delete_sync(inst, changes)

                mock_dispatch.assert_called_once()


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

    async def test_asave_recursion_guard(self):
        """Test that recursion guard works when _audit_in_progress is True."""
        inst = make_instance(audit_enabled=True)
        inst._audit_in_progress = True
        inst.__original_asave__ = AsyncMock(return_value="recurse_saved")

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()) as mocked:
            result = await AuditPatcher.asave(inst)

        # Should skip audit logic and just call original
        mocked.assert_not_called()
        assert result == "recurse_saved"


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

        qs.__original_adelete__ = AsyncMock(return_value=(1, {}))

        async def async_iter():
            yield obj

        qs._clone.return_value = qs
        qs.all.return_value = qs
        qs.__aiter__ = lambda *_: async_iter()

        with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"gone": True}):
            with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_delete", new=AsyncMock()) as mocked:
                await AuditPatcher.adelete_queryset(qs)

        # args, kwargs = mocked.call_args
        # assert kwargs["payload"]["changes"] == {"gone": True}
        mocked.assert_awaited_once()

    async def test_adelete_queryset_skips_when_audit_disabled(self):
        fake_model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(fake_model)
        qs.__original_adelete__ = AsyncMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_delete", new=AsyncMock()) as mocked:
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

    def test_sync_save_does_not_exist(self):
        # Case where pk exists but object is not found in DB (treated as new)
        inst = make_instance(audit_enabled=True)
        # inst.pk is "123" by default from make_instance

        inst.__original_save__ = MagicMock(return_value="saved")
        # Mock DoesNotExist exception
        inst.__class__.DoesNotExist = Exception
        inst.__class__.objects.get.side_effect = inst.__class__.DoesNotExist

        with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"x": 1}):
            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync") as mocked:
                result = AuditPatcher.save(inst)

        # Should be treated as create
        mocked.assert_called_once_with(inst, {"x": 1})
        assert result == "saved"

    def test_sync_save_recursion_guard(self):
        inst = make_instance(audit_enabled=True)
        inst._audit_in_progress = True
        inst.__original_save__ = MagicMock(return_value="recurse_saved_sync")

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync") as mocked:
            result = AuditPatcher.save(inst)

        mocked.assert_not_called()
        assert result == "recurse_saved_sync"


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
        qs.all.side_effect = [[old_obj], [new_obj]]

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
        qs.__original_delete__ = MagicMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"gone": True}):
            with patch("apps.audit_app.v1.patcher.async_to_sync", side_effect=lambda f: f):
                with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_delete") as mocked:
                    AuditPatcher.delete_queryset(qs)

        mocked.assert_called_once()

    def test_sync_delete_queryset_skips_when_disabled(self):
        model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(model)
        qs.__original_delete__ = MagicMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mocked:
            AuditPatcher.delete_queryset(qs)

        mocked.assert_not_called()


# ============================================================
#  DISPATCHER LOGIC (Empty checks)
# ============================================================


class TestAuditPatcherDispatchers:

    @pytest.mark.asyncio
    async def test_audit_update_async_skips_empty_changes(self):
        with patch("apps.audit_app.v1.services.AuditService.log_update", new=AsyncMock()) as mock_log:
            await AuditPatcher.audit_update_async(MagicMock(), {})
            mock_log.assert_not_called()

    def test_audit_update_sync_skips_empty_changes(self):
        with patch("apps.audit_app.v1.services.AuditService.log_update_sync") as mock_log:
            AuditPatcher.audit_update_sync(MagicMock(), {})
            mock_log.assert_not_called()


# ============================================================
#  ZERO IMPACT SCENARIOS (Coverage for early returns)
# ============================================================


class TestAuditPatcherZeroImpacts:

    @pytest.mark.asyncio
    async def test_aupdate_zero_impact(self):
        qs = make_qs(MagicMock(AUDIT_ENABLED=True))
        qs.__original_aupdate__ = AsyncMock(return_value=0)

        # Setup iterator for "before" snapshot
        async def async_iter():
            yield MagicMock()

        qs.all.return_value = qs
        qs.__aiter__ = lambda *args: async_iter()

        with patch(
            "apps.audit_app.v1.patcher.AuditPatcher.audit_update_async", new=AsyncMock()
        ) as mock_audit:
            await AuditPatcher.aupdate(qs)
            mock_audit.assert_not_called()

    @pytest.mark.asyncio
    async def test_adelete_queryset_zero_impact(self):
        qs = make_qs(MagicMock(AUDIT_ENABLED=True))
        qs.__original_adelete__ = AsyncMock(return_value=(0, {}))

        async def async_iter():
            yield MagicMock()

        qs.all.return_value = qs
        qs.__aiter__ = lambda *args: async_iter()

        with patch(
            "apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()
        ) as mock_audit:
            await AuditPatcher.adelete_queryset(qs)
            mock_audit.assert_not_called()

    def test_sync_update_zero_impact(self):
        qs = make_qs(MagicMock(AUDIT_ENABLED=True))
        qs.__original_update__ = MagicMock(return_value=0)

        qs._clone().all.return_value = [MagicMock()]

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync") as mock_audit:
            AuditPatcher.update(qs)
            mock_audit.assert_not_called()

    def test_sync_delete_queryset_zero_impact(self):
        qs = make_qs(MagicMock(AUDIT_ENABLED=True))
        qs.__original_delete__ = MagicMock(return_value=(0, {}))
        qs._clone().all.return_value = [MagicMock()]

        with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mock_audit:
            AuditPatcher.delete_queryset(qs)
            mock_audit.assert_not_called()
