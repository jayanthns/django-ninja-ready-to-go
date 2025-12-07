from unittest.mock import patch

from apps.audit_app.v1.tasks.dramatiq_tasks import (
    audit_log_create_dramatiq_task,
    audit_log_delete_dramatiq_task,
    audit_log_update_dramatiq_task,
)


class TestDramatiqTasks:

    @patch("apps.audit_app.v1.services.AuditService.log_create_sync")
    def test_create_task(self, mock_log):
        payload = {"d": 4}
        audit_log_create_dramatiq_task(payload)
        mock_log.assert_called_once_with(d=4)

    @patch("apps.audit_app.v1.services.AuditService.log_update_sync")
    def test_update_task(self, mock_log):
        payload = {"e": 5}
        audit_log_update_dramatiq_task(payload)
        mock_log.assert_called_once_with(e=5)

    @patch("apps.audit_app.v1.services.AuditService.log_delete_sync")
    def test_delete_task(self, mock_log):
        payload = {"f": 6}
        audit_log_delete_dramatiq_task(payload)
        mock_log.assert_called_once_with(f=6)
