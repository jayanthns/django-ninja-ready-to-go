from unittest.mock import AsyncMock, patch

import pytest

from apps.audit_app.v1.task_dispatcher import TaskDispatcher


class TestTaskDispatcher:

    @pytest.mark.asyncio
    async def test_dispatch_create_with_async_task(self):
        payload = {"x": 1}
        # Patch the imported task in the module
        with patch("apps.audit_app.v1.task_dispatcher.audit_log_create_task") as mock_task:
            await TaskDispatcher.dispatch_create(payload)
            mock_task.delay.assert_called_once_with({"x": 1, "changes": {}})

    @pytest.mark.asyncio
    async def test_dispatch_create_inline(self):
        payload = {"x": 1}
        # Simulate no async task configured
        with patch("apps.audit_app.v1.task_dispatcher.audit_log_create_task", new=None):
            with patch("apps.audit_app.v1.services.AuditService.log_create", new=AsyncMock()) as mock_service:
                await TaskDispatcher.dispatch_create(payload)
                mock_service.assert_awaited_once_with(x=1, changes={})

    @pytest.mark.asyncio
    async def test_dispatch_update_with_async_task(self):
        payload = {"y": 2}
        with patch("apps.audit_app.v1.task_dispatcher.audit_log_update_task") as mock_task:
            await TaskDispatcher.dispatch_update(payload)
            mock_task.delay.assert_called_once_with(payload)

    @pytest.mark.asyncio
    async def test_dispatch_update_inline(self):
        payload = {"y": 2}
        with patch("apps.audit_app.v1.task_dispatcher.audit_log_update_task", new=None):
            with patch("apps.audit_app.v1.services.AuditService.log_update", new=AsyncMock()) as mock_service:
                await TaskDispatcher.dispatch_update(payload)
                mock_service.assert_awaited_once_with(y=2)

    @pytest.mark.asyncio
    async def test_dispatch_delete_with_async_task(self):
        payload = {"z": 3}
        with patch("apps.audit_app.v1.task_dispatcher.audit_log_delete_task") as mock_task:
            await TaskDispatcher.dispatch_delete(payload)
            mock_task.delay.assert_called_once_with(payload)

    @pytest.mark.asyncio
    async def test_dispatch_delete_inline(self):
        payload = {"z": 3}
        with patch("apps.audit_app.v1.task_dispatcher.audit_log_delete_task", new=None):
            with patch("apps.audit_app.v1.services.AuditService.log_delete", new=AsyncMock()) as mock_service:
                await TaskDispatcher.dispatch_delete(payload)
                mock_service.assert_awaited_once_with(z=3)
