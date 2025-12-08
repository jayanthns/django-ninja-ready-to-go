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
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

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

                    mock_logger.info.assert_any_call("[1] Entering AuditPatcher.audit_create_async")
                    mock_logger.info.assert_any_call("[2] Exiting AuditPatcher.audit_create_async")

    @pytest.mark.asyncio
    async def test_audit_update_async_internals(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

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
                    args, kwargs = mock_dispatch.call_args
                    assert kwargs["payload"]["changes"] == changes

                    mock_logger.info.assert_any_call("[1] Entering AuditPatcher.audit_update_async")
                    mock_logger.info.assert_any_call("[2] Exiting AuditPatcher.audit_update_async")

    @pytest.mark.asyncio
    async def test_audit_delete_async_internals(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

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

                    mock_logger.info.assert_any_call("[1] Entering AuditPatcher.audit_delete_async")
                    mock_logger.info.assert_any_call("[2] Exiting AuditPatcher.audit_delete_async")

    def test_audit_create_sync_internals(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={"user": "test3"}):
                with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_create") as mock_dispatch:
                    with patch("apps.audit_app.v1.patcher.async_to_sync", side_effect=lambda f: f):
                        mock_dispatch = MagicMock()
                        with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_create", mock_dispatch):
                            inst = MagicMock()
                            inst._meta.app_label = "app"
                            inst._meta.model_name = "model"
                            inst.pk = "4"
                            changes = {"a": 1}

                            AuditPatcher.audit_create_sync(inst, changes)

                            mock_dispatch.assert_called_once()

                            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.audit_create_sync")
                            mock_logger.info.assert_any_call("[2] Exiting AuditPatcher.audit_create_sync")

    def test_audit_update_sync_internals(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch("apps.audit_app.v1.patcher.async_to_sync", side_effect=lambda f: f):
                with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_update") as mock_dispatch:
                    with patch(
                        "apps.audit_app.v1.patcher.get_normalized_context", return_value={"user": "test1"}
                    ):
                        inst = MagicMock()
                        inst._meta.app_label = "app"
                        inst._meta.model_name = "model"
                        inst.pk = "5"
                        changes = {"b": 2}
                        AuditPatcher.audit_update_sync(inst, changes)

                        mock_dispatch.assert_called_once()
                        mock_logger.info.assert_any_call("[1] Entering AuditPatcher.audit_update_sync")
                        mock_logger.info.assert_any_call("[2] Exiting AuditPatcher.audit_update_sync")

    def test_audit_delete_sync_internals(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch("apps.audit_app.v1.patcher.async_to_sync", side_effect=lambda f: f):
                with patch("apps.audit_app.v1.patcher.TaskDispatcher.dispatch_delete") as mock_dispatch:
                    with patch(
                        "apps.audit_app.v1.patcher.get_normalized_context", return_value={"user": "test2"}
                    ):
                        inst = MagicMock()
                        inst._meta.app_label = "app"
                        inst._meta.model_name = "model"
                        inst.pk = "6"
                        changes = {"c": 3}
                        AuditPatcher.audit_delete_sync(inst, changes)

                        mock_dispatch.assert_called_once()
                        mock_logger.info.assert_any_call("[1] Entering AuditPatcher.audit_delete_sync")
                        mock_logger.info.assert_any_call("[2] Exiting AuditPatcher.audit_delete_sync")


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

    @pytest.mark.asyncio
    async def test_asave_create_calls_log_create(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.asave")
            mock_logger.info.assert_any_call("[2] Checking existing instance for asave")
            mock_logger.info.assert_any_call("[3] Auditing creation in asave")
            mock_logger.info.assert_any_call("[4] Exiting AuditPatcher.asave")

    async def test_asave_update_calls_log_update(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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
            mock_logger.info.assert_any_call("[3] Auditing update in asave")
            mock_logger.info.assert_any_call("[4] Exiting AuditPatcher.asave")

    async def test_asave_respects_audit_disabled(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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
            mock_logger.info.assert_any_call("[3] Audit disabled for model, exiting asave")

    async def test_asave_recursion_guard(self):
        """Test that recursion guard works when _audit_in_progress is True."""
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            inst = make_instance(audit_enabled=True)
            inst._audit_in_progress = True
            inst.__original_asave__ = AsyncMock(return_value="recurse_saved")

            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()
            ) as mocked:
                result = await AuditPatcher.asave(inst)

            # Should skip audit logic and just call original
            mocked.assert_not_called()
            assert result == "recurse_saved"

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.asave")
            mock_logger.info.assert_any_call("[2] Recursion detected in asave, skipping audit")


# ============================================================
#  ASYNC: adelete()
# ============================================================


@pytest.mark.asyncio
class TestAuditPatcherADelete:

    async def test_adelete_calls_log_delete(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            inst = make_instance(audit_enabled=True)
            inst.__original_adelete__ = AsyncMock(return_value="deleted")

            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"y": 9}):
                with patch(
                    "apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()
                ) as mocked:
                    result = await AuditPatcher.adelete(inst)

            mocked.assert_awaited_once_with(inst, {"y": 9})
            assert result == "deleted"

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.adelete")
            mock_logger.info.assert_any_call("[2] Auditing deletion in adelete")
            mock_logger.info.assert_any_call("[3] Exiting AuditPatcher.adelete")

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
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            fake_model = MagicMock(AUDIT_ENABLED=True)
            qs = make_qs(fake_model)
            old_obj = MagicMock()
            new_obj = MagicMock()
            new_obj.pk = "22"

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

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.aupdate")
            mock_logger.info.assert_any_call(f"[3] Auditing update for object: {new_obj.pk}")
            mock_logger.info.assert_any_call("[4] Exiting AuditPatcher.aupdate")

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
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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
                with patch(
                    "apps.audit_app.v1.patcher.TaskDispatcher.dispatch_delete", new=AsyncMock()
                ) as mocked:
                    await AuditPatcher.adelete_queryset(qs)

            mocked.assert_awaited_once()

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.adelete_queryset")
            mock_logger.info.assert_any_call("[2] Auditing queryset deletion")
            mock_logger.info.assert_any_call("[3] Exiting AuditPatcher.adelete_queryset")

    async def test_adelete_queryset_skips_when_audit_disabled(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            inst = make_instance(audit_enabled=True)
            inst.pk = None  # New object
            inst.__original_save__ = MagicMock(return_value="saved")

            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"x": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync") as mocked:
                    result = AuditPatcher.save(inst)

            mocked.assert_called_once_with(inst, {"x": 1})
            assert result == "saved"

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.save")
            mock_logger.info.assert_any_call("[2] Checking existing instance for save")
            mock_logger.info.assert_any_call("[3] Auditing creation in save")
            mock_logger.info.assert_any_call("[4] Exiting AuditPatcher.save")

    def test_sync_save_update(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            inst = make_instance(audit_enabled=True)
            old_obj = MagicMock()

            inst.__original_save__ = MagicMock(return_value="saved")
            inst.__class__.objects.get = MagicMock(return_value=old_obj)

            with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"u": 44}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync") as mocked:
                    AuditPatcher.save(inst)

            mocked.assert_called_once_with(inst, {"u": 44})
            mock_logger.info.assert_any_call("[3] Auditing update in save")
            mock_logger.info.assert_any_call("[4] Exiting AuditPatcher.save")

    def test_sync_save_skips_when_disabled(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            inst = make_instance(audit_enabled=False)
            inst.__original_save__ = MagicMock()

            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync") as mocked:
                AuditPatcher.save(inst)

            mocked.assert_not_called()
            mock_logger.info.assert_any_call("[3] Audit disabled for model, exiting save")

    def test_sync_save_does_not_exist(self):
        # Case where pk exists but object is not found in DB (treated as new)
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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

            mock_logger.info.assert_any_call("[3] Auditing creation in save")

    def test_sync_save_recursion_guard(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            inst = make_instance(audit_enabled=True)
            inst._audit_in_progress = True
            inst.__original_save__ = MagicMock(return_value="recurse_saved_sync")

            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync") as mocked:
                result = AuditPatcher.save(inst)

            mocked.assert_not_called()
            assert result == "recurse_saved_sync"
            mock_logger.info.assert_any_call("[2] Recursion detected in save, skipping audit")


class TestAuditPatcherSyncDelete:

    def test_sync_delete(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            inst = make_instance(True)
            inst.__original_delete__ = MagicMock(return_value="deleted")

            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"gone": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mocked:
                    AuditPatcher.delete(inst)

            mocked.assert_called_once_with(inst, {"gone": 1})

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.delete")
            mock_logger.info.assert_any_call("[2] Auditing deletion in delete")
            mock_logger.info.assert_any_call("[3] Exiting AuditPatcher.delete")

    def test_sync_delete_skips_when_disabled(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            inst = make_instance(False)
            inst.__original_delete__ = MagicMock()

            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mocked:
                AuditPatcher.delete(inst)

            mocked.assert_not_called()


class TestAuditPatcherSyncUpdate:

    def test_sync_update(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            model = MagicMock(AUDIT_ENABLED=True)
            qs = make_qs(model)

            old_obj = MagicMock()
            new_obj = MagicMock()
            new_obj.pk = "33"
            qs._clone().all.return_value = [old_obj]
            qs.__original_update__ = MagicMock(return_value=1)

            qs._clone.side_effect = [qs, qs]  # before, after
            qs.all.side_effect = [[old_obj], [new_obj]]

            with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"k": 7}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync") as mocked:
                    AuditPatcher.update(qs)

            mocked.assert_called_once_with(new_obj, {"k": 7})

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.update")
            mock_logger.info.assert_any_call(f"[3] Auditing update for object: {new_obj.pk}")
            mock_logger.info.assert_any_call("[4] Exiting AuditPatcher.update")

    def test_sync_update_skips_when_disabled(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            model = MagicMock(AUDIT_ENABLED=False)
            qs = make_qs(model)
            qs.__original_update__ = MagicMock(return_value=1)

            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync") as mocked:
                AuditPatcher.update(qs)

            mocked.assert_not_called()


class TestAuditPatcherSyncDeleteQueryset:

    def test_sync_delete_queryset(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.delete_queryset")
            mock_logger.info.assert_any_call("[2] Auditing queryset deletion")
            mock_logger.info.assert_any_call("[3] Exiting AuditPatcher.delete_queryset")

    def test_sync_delete_queryset_skips_when_disabled(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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
    @pytest.mark.asyncio
    async def test_aupdate_zero_impact(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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

            mock_logger.info.assert_any_call("[2] No records updated in aupdate")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_adelete_queryset_zero_impact(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
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

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.adelete_queryset")
            mock_logger.info.assert_any_call("[3] Exiting AuditPatcher.adelete_queryset")

    def test_sync_update_zero_impact(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            qs = make_qs(MagicMock(AUDIT_ENABLED=True))
            qs.__original_update__ = MagicMock(return_value=0)

            qs._clone().all.return_value = [MagicMock()]

            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync") as mock_audit:
                AuditPatcher.update(qs)
                mock_audit.assert_not_called()

            mock_logger.info.assert_any_call("[2] No records updated in update")

    def test_sync_delete_queryset_zero_impact(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            qs = make_qs(MagicMock(AUDIT_ENABLED=True))
            qs.__original_delete__ = MagicMock(return_value=(0, {}))
            qs._clone().all.return_value = [MagicMock()]

            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mock_audit:
                AuditPatcher.delete_queryset(qs)
                mock_audit.assert_not_called()

            mock_logger.info.assert_any_call("[1] Entering AuditPatcher.delete_queryset")
            mock_logger.info.assert_any_call("[3] Exiting AuditPatcher.delete_queryset")


# ============================================================
#  NO LOGGER SCENARIOS (Coverage for None logger)
# ============================================================


class TestAuditPatcherNoLogger:

    @pytest.mark.asyncio
    async def test_async_internals_no_logger(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=None):
            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={}):
                with patch("apps.audit_app.v1.patcher.TaskDispatcher") as mock_disp:
                    mock_disp.dispatch_create = AsyncMock()
                    mock_disp.dispatch_update = AsyncMock()
                    mock_disp.dispatch_delete = AsyncMock()

                    # Async internals
                    inst = MagicMock()
                    await AuditPatcher.audit_create_async(inst, {"a": 1})
                    await AuditPatcher.audit_update_async(inst, {"b": 2})
                    await AuditPatcher.audit_delete_async(inst, {"c": 3})

    def test_sync_internals_no_logger(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=None):
            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={}):
                with patch("apps.audit_app.v1.patcher.async_to_sync", side_effect=lambda f: f):
                    with patch("apps.audit_app.v1.patcher.TaskDispatcher"):
                        inst = MagicMock()
                        AuditPatcher.audit_create_sync(inst, {"a": 1})
                        AuditPatcher.audit_update_sync(inst, {"b": 2})
                        AuditPatcher.audit_delete_sync(inst, {"c": 3})

    @pytest.mark.asyncio
    async def test_edge_cases_no_logger(self):
        """Cover recursion guard and audit disabled checks when logger is None."""
        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=None):
            # 1. Recursion guard
            inst_recurse = make_instance(audit_enabled=True)
            inst_recurse._audit_in_progress = True
            inst_recurse.__original_asave__ = AsyncMock(return_value="recurse")
            inst_recurse.__original_save__ = MagicMock(return_value="recurse")

            await AuditPatcher.asave(inst_recurse)
            AuditPatcher.save(inst_recurse)
            # Assertions: should not crash, should return result

            # 2. Audit Disabled
            inst_disabled = make_instance(audit_enabled=False)
            inst_disabled.__original_asave__ = AsyncMock(return_value="disabled")
            inst_disabled.__original_save__ = MagicMock(return_value="disabled")
            inst_disabled.__original_adelete__ = AsyncMock(return_value="disabled")
            inst_disabled.__original_delete__ = MagicMock(return_value="disabled")

            await AuditPatcher.asave(inst_disabled)
            await AuditPatcher.adelete(inst_disabled)
            AuditPatcher.save(inst_disabled)
            AuditPatcher.delete(inst_disabled)

            # 3. Disabled QuerySet
            fake_model = MagicMock(AUDIT_ENABLED=False)
            qs = make_qs(fake_model)
            qs.__original_aupdate__ = AsyncMock(return_value=1)
            qs.__original_adelete__ = AsyncMock(return_value=(1, {}))

            await AuditPatcher.aupdate(qs)
            await AuditPatcher.adelete_queryset(qs)

    @pytest.mark.asyncio
    async def test_model_patches_no_logger(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=None):
            inst = make_instance(audit_enabled=True)
            inst.__original_asave__ = AsyncMock(return_value="saved")
            inst.__original_adelete__ = AsyncMock(return_value="deleted")

            # Use AsyncMock for aget to support Update path
            inst.__class__.objects.aget = AsyncMock(return_value=MagicMock())

            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={}):
                with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={}):
                    with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()):
                        with patch(
                            "apps.audit_app.v1.patcher.AuditPatcher.audit_update_async", new=AsyncMock()
                        ):
                            await AuditPatcher.asave(inst)

            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()):
                    await AuditPatcher.adelete(inst)

            # Sync patches
            inst.__original_save__ = MagicMock(return_value="saved")
            inst.__original_delete__ = MagicMock(return_value="deleted")

            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync"):
                    AuditPatcher.save(inst)

            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync"):
                    AuditPatcher.delete(inst)

    @pytest.mark.asyncio
    async def test_create_and_zero_impact_no_logger(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=None):
            # 1. Create (pk=None) - Async
            inst_new = make_instance(audit_enabled=True)
            inst_new.pk = None
            inst_new.__original_asave__ = AsyncMock(return_value="saved")

            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()):
                    await AuditPatcher.asave(inst_new)

            # 2. Create (pk=None) - Sync
            inst_new_sync = make_instance(audit_enabled=True)
            inst_new_sync.pk = None
            inst_new_sync.__original_save__ = MagicMock(return_value="saved")

            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync"):
                    AuditPatcher.save(inst_new_sync)

            # 3. Zero Impact Update - Async
            qs = make_qs(MagicMock(AUDIT_ENABLED=True))
            qs.__original_aupdate__ = AsyncMock(return_value=0)
            # aiter needs to yield objects, but if update returns 0, it calls _clone().all() (which we mocked)?
            # Logic: if updated == 0: logger... return updated.
            # So it does NOT iterate. It calls `await self.__original_aupdate__(**kwargs)`.
            # If 0, it enters zero impact block.

            async def async_iter():
                yield MagicMock()

            qs.all.return_value = qs
            qs.__aiter__ = lambda *_: async_iter()

            await AuditPatcher.aupdate(qs)

            # 4. Zero Impact Update - Sync
            qs_sync = make_qs(MagicMock(AUDIT_ENABLED=True))
            qs_sync.__original_update__ = MagicMock(return_value=0)
            qs_sync.all.return_value = qs_sync
            qs_sync.__iter__ = lambda *_: iter([MagicMock()])

            AuditPatcher.update(qs_sync)

    @pytest.mark.asyncio
    async def test_queryset_patches_no_logger(self):
        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=None):
            fake_model = MagicMock(AUDIT_ENABLED=True)
            qs = make_qs(fake_model)
            qs.__original_aupdate__ = AsyncMock(return_value=1)
            qs.__original_adelete__ = AsyncMock(return_value=(1, {}))
            qs.__original_update__ = MagicMock(return_value=1)
            qs.__original_delete__ = MagicMock(return_value=(1, {}))

            async def async_iter():
                yield MagicMock()

            qs.all.return_value = qs
            qs.__aiter__ = lambda *_: async_iter()
            qs._clone.return_value = qs

            # For sync update/delete_queryset, we need list() support
            qs.__iter__ = lambda *_: iter([MagicMock()])

            with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"change": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_async", new=AsyncMock()):
                    await AuditPatcher.aupdate(qs)

            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"change": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()):
                    await AuditPatcher.adelete_queryset(qs)

            # Sync QS
            with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"change": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync"):
                    AuditPatcher.update(qs)

            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"change": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync"):
                    AuditPatcher.delete_queryset(qs)
