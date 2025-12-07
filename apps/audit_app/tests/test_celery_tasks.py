from unittest.mock import patch

from apps.audit_app.v1.tasks.celery_tasks import (
    audit_log_create_celery_task,
    audit_log_delete_celery_task,
    audit_log_update_celery_task,
)


class TestCeleryTasks:

    @patch("apps.audit_app.v1.services.AuditService.log_create_sync")
    def test_create_task(self, mock_log):
        payload = {"a": 1}
        audit_log_create_celery_task(payload)
        mock_log.assert_called_once_with(a=1)

    @patch("apps.audit_app.v1.services.AuditService.log_update_sync")
    def test_update_task(self, mock_log):
        payload = {"b": 2}
        audit_log_update_celery_task(payload)
        mock_log.assert_called_once_with(b=2)

    @patch("apps.audit_app.v1.services.AuditService.log_delete_sync")
    def test_delete_task(self, mock_log):
        payload = {"c": 3}
        audit_log_delete_celery_task(payload)
        mock_log.assert_called_once_with(c=3)
