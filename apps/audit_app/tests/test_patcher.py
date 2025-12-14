from unittest.mock import AsyncMock, call, MagicMock, patch

import pytest

from apps.audit_app.v1.patcher import AuditPatcher
from apps.audit_app.v1.task_dispatcher import TaskDispatcher

# ============================================================
#  HELPERS
# ============================================================


def make_instance(audit_enabled=True, pk="123"):
    inst = MagicMock()
    inst.pk = pk
    inst.AUDIT_ENABLED = audit_enabled
    inst._audit_in_progress = False
    inst.__class__.DoesNotExist = Exception
    inst.__class__.objects = MagicMock()
    return inst


def make_qs(model):
    qs = MagicMock()
    qs.model = model
    qs._clone.return_value = qs
    return qs


# ============================================================
#  ASYNC AUDIT DISPATCHERS
# ============================================================


class TestAuditAsyncDispatchers:

    @pytest.mark.asyncio
    async def test_audit_create_async_logs(self):
        logger = MagicMock()
        inst = MagicMock()
        inst._meta.app_label = "app"
        inst._meta.model_name = "model"
        inst.pk = "1"

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={}):
                with patch(
                    "apps.audit_app.v1.patcher.TaskDispatcher.dispatch_create",
                    new=AsyncMock(),
                ) as mocked:
                    await AuditPatcher.audit_create_async(inst, {"a": 1})

        mocked.assert_awaited_once()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.audit_create_async"),
                call("[2] Exiting AuditPatcher.audit_create_async"),
            ]
        )

    @pytest.mark.asyncio
    async def test_audit_update_async_logs(self):
        logger = MagicMock()
        inst = MagicMock()
        inst._meta.app_label = "app"
        inst._meta.model_name = "model"
        inst.pk = "2"

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={}):
                with patch(
                    "apps.audit_app.v1.patcher.TaskDispatcher.dispatch_update",
                    new=AsyncMock(),
                ) as mocked:
                    await AuditPatcher.audit_update_async(inst, {"b": 2})

        mocked.assert_awaited_once()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.audit_update_async"),
                call("[2] Exiting AuditPatcher.audit_update_async"),
            ]
        )

    @pytest.mark.asyncio
    async def test_audit_update_async_empty_changes(self):
        # Should return early before logger usage
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            await AuditPatcher.audit_update_async(MagicMock(), {})
            mock_get_logger.assert_not_called()

    @pytest.mark.asyncio
    async def test_audit_delete_async_logs(self):
        logger = MagicMock()
        inst = MagicMock()
        inst._meta.app_label = "app"
        inst._meta.model_name = "model"
        inst.pk = "3"

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={}):
                with patch(
                    "apps.audit_app.v1.patcher.TaskDispatcher.dispatch_delete",
                    new=AsyncMock(),
                ) as mocked:
                    await AuditPatcher.audit_delete_async(inst, {"c": 3})

        mocked.assert_awaited_once()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.audit_delete_async"),
                call("[2] Exiting AuditPatcher.audit_delete_async"),
            ]
        )


# ============================================================
#  ASYNC INSTANCE SAVE
# ============================================================


class TestAuditAsyncSave:

    @pytest.mark.asyncio
    async def test_asave_create_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=True, pk=None)
        inst.__original_asave__ = AsyncMock(return_value="saved")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"x": 1}):
                with patch(
                    "apps.audit_app.v1.patcher.AuditPatcher.audit_create_async",
                    new=AsyncMock(),
                ):
                    result = await AuditPatcher.asave(inst)

        assert result == "saved"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.asave"),
                call("[3] Auditing creation in asave"),
                call("[4] Exiting AuditPatcher.asave"),
            ]
        )

    @pytest.mark.asyncio
    async def test_asave_update_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=True)
        inst.__original_asave__ = AsyncMock(return_value="saved")
        inst.__class__.objects.aget = AsyncMock(return_value=MagicMock())

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"u": 1}):
                with patch(
                    "apps.audit_app.v1.patcher.AuditPatcher.audit_update_async",
                    new=AsyncMock(),
                ):
                    await AuditPatcher.asave(inst)

        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.asave"),
                call("[3] Auditing update in asave"),
                call("[4] Exiting AuditPatcher.asave"),
            ]
        )

    @pytest.mark.asyncio
    async def test_asave_recursion_guard_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=True)
        inst._audit_in_progress = True
        inst.__original_asave__ = AsyncMock(return_value="saved")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            result = await AuditPatcher.asave(inst)

        assert result == "saved"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.asave"),
                call("[2] Recursion detected in asave, skipping audit"),
            ]
        )

    @pytest.mark.asyncio
    async def test_asave_disabled_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=False)
        inst.__original_asave__ = AsyncMock(return_value="saved")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            result = await AuditPatcher.asave(inst)

        assert result == "saved"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.asave"),
                call("[3] Audit disabled for model, exiting asave"),
            ]
        )


# ============================================================
#  SYNC INSTANCE SAVE
# ============================================================


class TestAuditSyncSave:

    def test_save_create_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=True, pk=None)
        inst.__original_save__ = MagicMock(return_value="saved")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"x": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync"):
                    result = AuditPatcher.save(inst)

        assert result == "saved"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.save"),
                call("[3] Auditing creation in save"),
                call("[4] Exiting AuditPatcher.save"),
            ]
        )

    def test_save_update_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=True)
        inst.__original_save__ = MagicMock(return_value="saved")
        inst.__class__.objects.get = MagicMock(return_value=MagicMock())

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_update_diff", return_value={"u": 2}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_update_sync"):
                    AuditPatcher.save(inst)

        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.save"),
                call("[3] Auditing update in save"),
                call("[4] Exiting AuditPatcher.save"),
            ]
        )

    def test_save_recursion_guard_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=True)
        inst._audit_in_progress = True
        inst.__original_save__ = MagicMock(return_value="saved")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            result = AuditPatcher.save(inst)

        assert result == "saved"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.save"),
                call("[2] Recursion detected in save, skipping audit"),
            ]
        )

    def test_save_disabled_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=False)
        inst.__original_save__ = MagicMock(return_value="saved")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            result = AuditPatcher.save(inst)

        assert result == "saved"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.save"),
                call("[3] Audit disabled for model, exiting save"),
            ]
        )

    def test_save_update_missing_record(self):
        # Covers the DoesNotExist block -> treats as create
        logger = MagicMock()
        inst = make_instance(audit_enabled=True, pk="999")
        inst.__original_save__ = MagicMock(return_value="saved")
        # Simulate record missing in DB
        inst.__class__.objects.get.side_effect = inst.__class__.DoesNotExist

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"x": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_sync"):
                    result = AuditPatcher.save(inst)

        assert result == "saved"
        # Should call audit_create_sync, NOT update
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.save"),
                call("[3] Auditing creation in save"),
                call("[4] Exiting AuditPatcher.save"),
            ]
        )

    @pytest.mark.asyncio
    async def test_asave_update_missing_record(self):
        # Covers the DoesNotExist block in async save -> treats as create
        logger = MagicMock()
        inst = make_instance(audit_enabled=True, pk="9999")
        inst.__original_asave__ = AsyncMock(return_value="saved")
        # Simulate record missing in DB
        inst.__class__.objects.aget.side_effect = inst.__class__.DoesNotExist

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_create_diff", return_value={"x": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_create_async", new=AsyncMock()):
                    result = await AuditPatcher.asave(inst)

        assert result == "saved"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.asave"),
                call("[3] Auditing creation in asave"),
                call("[4] Exiting AuditPatcher.asave"),
            ]
        )


# ============================================================
#  SYNC AUDIT DISPATCHERS
# ============================================================


class TestAuditSyncDispatchers:
    def test_audit_update_sync_empty_changes(self):
        # Should return early before logger usage
        with patch("apps.audit_app.v1.patcher.get_request_logger") as mock_get_logger:
            AuditPatcher.audit_update_sync(MagicMock(), {})
            mock_get_logger.assert_not_called()

    def test_audit_create_sync_logs(self):
        logger = MagicMock()
        inst = MagicMock()
        inst._meta.app_label = "app"
        inst._meta.model_name = "model"
        inst.pk = "101"

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={}):
                with patch("apps.audit_app.v1.patcher.async_to_sync") as mock_a2s:
                    mock_dispatch = MagicMock()
                    mock_a2s.return_value = mock_dispatch
                    AuditPatcher.audit_create_sync(inst, {"a": 1})

        mock_a2s.assert_called_with(TaskDispatcher.dispatch_create)
        mock_dispatch.assert_called_once()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.audit_create_sync"),
                call("[2] Exiting AuditPatcher.audit_create_sync"),
            ]
        )

    def test_audit_update_sync_logs(self):
        logger = MagicMock()
        inst = MagicMock()
        inst._meta.app_label = "app"
        inst._meta.model_name = "model"
        inst.pk = "102"

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={}):
                with patch("apps.audit_app.v1.patcher.async_to_sync") as mock_a2s:
                    mock_dispatch = MagicMock()
                    mock_a2s.return_value = mock_dispatch
                    # Non-empty changes to ensure we pass the 'if not changes' check
                    AuditPatcher.audit_update_sync(inst, {"b": 2})

        mock_a2s.assert_called_with(TaskDispatcher.dispatch_update)
        mock_dispatch.assert_called_once()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.audit_update_sync"),
                call("[2] Exiting AuditPatcher.audit_update_sync"),
            ]
        )

    def test_audit_delete_sync_logs(self):
        logger = MagicMock()
        inst = MagicMock()
        inst._meta.app_label = "app"
        inst._meta.model_name = "model"
        inst.pk = "103"

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.get_normalized_context", return_value={}):
                with patch("apps.audit_app.v1.patcher.async_to_sync") as mock_a2s:
                    mock_dispatch = MagicMock()
                    mock_a2s.return_value = mock_dispatch
                    AuditPatcher.audit_delete_sync(inst, {"c": 3})

        mock_a2s.assert_called_with(TaskDispatcher.dispatch_delete)
        mock_dispatch.assert_called_once()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.audit_delete_sync"),
                call("[2] Exiting AuditPatcher.audit_delete_sync"),
            ]
        )


# ============================================================
#  QUERYSET UPDATE VIOLATIONS
# ============================================================


class TestAuditQuerySetUpdateViolations:

    @pytest.mark.asyncio
    async def test_aupdate_violation_logs(self):
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=True)
        model.__name__ = "Animal"  # ✅ FIX
        qs = make_qs(model)
        qs.__original_aupdate__ = AsyncMock()

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with pytest.raises(RuntimeError):
                await AuditPatcher.aupdate(qs)

        logger.error.assert_called_once()
        logger.info.assert_any_call("[1] Entering AuditPatcher.aupdate")

    def test_update_violation_logs(self):
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=True)
        model.__name__ = "Animal"  # ✅ FIX
        qs = make_qs(model)
        qs.__original_update__ = MagicMock()

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with pytest.raises(RuntimeError):
                AuditPatcher.update(qs)

        logger.error.assert_called_once()
        logger.info.assert_any_call("[1] Entering AuditPatcher.update")

    @pytest.mark.asyncio
    async def test_aupdate_disabled_success(self):
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(model)
        qs.__original_aupdate__ = AsyncMock(return_value=5)

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            result = await AuditPatcher.aupdate(qs)

        assert result == 5
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.aupdate"),
                call("[3] Exiting AuditPatcher.aupdate"),
            ]
        )

    def test_update_disabled_success(self):
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(model)
        qs.__original_update__ = MagicMock(return_value=5)

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            result = AuditPatcher.update(qs)

        assert result == 5
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.update"),
                call("[3] Exiting AuditPatcher.update"),
            ]
        )


# ============================================================
#  QUERYSET DELETE
# ============================================================


class TestAuditQuerySetDelete:

    @pytest.mark.asyncio
    async def test_adelete_queryset_logs(self):
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=True)
        qs = make_qs(model)
        qs.__original_adelete__ = AsyncMock(return_value=(1, {}))

        # IMPORTANT: Fix the mock so async for loop actually runs
        # We need qs._clone().all() to return an object that has an __aiter__
        # make_qs sets _clone.return_value = qs
        # So we need qs.all() to return qs (or something iterable)
        qs.all.return_value = qs

        async def async_iter():
            yield MagicMock()

        qs.__aiter__ = lambda *_: async_iter()

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"d": 1}):
                with patch(
                    "apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async",
                    new=AsyncMock(),
                ):
                    await AuditPatcher.adelete_queryset(qs)

        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.adelete_queryset"),
                call("[2] Auditing queryset deletion"),
                call("[3] Exiting AuditPatcher.adelete_queryset"),
            ]
        )

    @pytest.mark.asyncio
    async def test_adelete_queryset_nothing_deleted(self):
        # Covers the case where deleted is False (0)
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=True)
        qs = make_qs(model)
        qs.__original_adelete__ = AsyncMock(return_value=(0, {}))

        qs.all.return_value = qs

        async def async_iter():
            # No items
            if False:
                yield MagicMock()

        qs.__aiter__ = lambda *_: async_iter()

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            # Should NOT call compute_delete_diff or audit_delete_async due to early exit (if deleted is False)
            # Actually logic is if deleted: ...
            await AuditPatcher.adelete_queryset(qs)

        # We verify that we skipped the audit block
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.adelete_queryset"),
                # Missing "[2] Auditing queryset deletion"
                call("[3] Exiting AuditPatcher.adelete_queryset"),
            ]
        )

    @pytest.mark.asyncio
    async def test_adelete_queryset_disabled_logs(self):
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(model)
        qs.__original_adelete__ = AsyncMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()
            ) as mock_audit:
                result = await AuditPatcher.adelete_queryset(qs)

        assert result == (1, {})
        mock_audit.assert_not_called()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.adelete_queryset"),
                call("[2] Exiting AuditPatcher.adelete_queryset"),
            ]
        )

    def test_delete_queryset_logs(self):
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=True)
        qs = make_qs(model)
        qs.__original_delete__ = MagicMock(return_value=(1, {}))
        qs._clone().all.return_value = [MagicMock()]

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"d": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync"):
                    AuditPatcher.delete_queryset(qs)

        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.delete_queryset"),
                call("[2] Auditing queryset deletion"),
                call("[3] Exiting AuditPatcher.delete_queryset"),
            ]
        )

    def test_delete_queryset_nothing_deleted(self):
        # Covers sync delete_queryset where deleted is False/(0, {})
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=True)
        qs = make_qs(model)
        qs.__original_delete__ = MagicMock(return_value=(0, {}))
        qs._clone().all.return_value = (
            []
        )  # Empty because nothing deleted usually implies empty or condition not met

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            AuditPatcher.delete_queryset(qs)

        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.delete_queryset"),
                # Missing "[2] Auditing queryset deletion"
                call("[3] Exiting AuditPatcher.delete_queryset"),
            ]
        )

    def test_delete_queryset_disabled_logs(self):
        logger = MagicMock()
        model = MagicMock(AUDIT_ENABLED=False)
        qs = make_qs(model)
        qs.__original_delete__ = MagicMock(return_value=(1, {}))

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mock_audit:
                result = AuditPatcher.delete_queryset(qs)

        assert result == (1, {})
        mock_audit.assert_not_called()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.delete_queryset"),
                call("[2] Exiting AuditPatcher.delete_queryset"),
            ]
        )


# ============================================================
#  INSTANCE DELETE (ASYNC + SYNC)
# ============================================================


class TestAuditInstanceDelete:

    @pytest.mark.asyncio
    async def test_adelete_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=True)
        inst.__original_adelete__ = AsyncMock(return_value="deleted")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"d": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()):
                    result = await AuditPatcher.adelete(inst)

        assert result == "deleted"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.adelete"),
                call("[2] Auditing deletion in adelete"),
                call("[3] Exiting AuditPatcher.adelete"),
            ]
        )

    @pytest.mark.asyncio
    async def test_adelete_disabled_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=False)
        inst.__original_adelete__ = AsyncMock(return_value="deleted")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch(
                "apps.audit_app.v1.patcher.AuditPatcher.audit_delete_async", new=AsyncMock()
            ) as mock_audit:
                result = await AuditPatcher.adelete(inst)

        assert result == "deleted"
        mock_audit.assert_not_called()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.adelete"),
                call("[3] Exiting AuditPatcher.adelete"),
            ]
        )

    def test_delete_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=True)
        inst.__original_delete__ = MagicMock(return_value="deleted")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.compute_delete_diff", return_value={"d": 1}):
                with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync"):
                    result = AuditPatcher.delete(inst)

        assert result == "deleted"
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.delete"),
                call("[2] Auditing deletion in delete"),
                call("[3] Exiting AuditPatcher.delete"),
            ]
        )

    def test_delete_disabled_logs(self):
        logger = MagicMock()
        inst = make_instance(audit_enabled=False)
        inst.__original_delete__ = MagicMock(return_value="deleted")

        with patch("apps.audit_app.v1.patcher.get_request_logger", return_value=logger):
            with patch("apps.audit_app.v1.patcher.AuditPatcher.audit_delete_sync") as mock_audit:
                result = AuditPatcher.delete(inst)

        assert result == "deleted"
        mock_audit.assert_not_called()
        logger.info.assert_has_calls(
            [
                call("[1] Entering AuditPatcher.delete"),
                call("[3] Exiting AuditPatcher.delete"),
            ]
        )
