from unittest.mock import AsyncMock, call, MagicMock, patch

import pytest

from apps.audit_app.v1.patcher import AuditPatcher

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
