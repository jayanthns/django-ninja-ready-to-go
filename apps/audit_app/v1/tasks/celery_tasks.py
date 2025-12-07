from celery import shared_task

from apps.audit_app.v1.services import AuditService


@shared_task(bind=True)
def audit_log_create_celery_task(self, payload: dict):
    print("audit_log_create_celery_task")
    print(payload)
    AuditService.log_create_sync(**payload)


@shared_task(bind=True)
def audit_log_update_celery_task(self, payload: dict):
    AuditService.log_update_sync(**payload)


@shared_task(bind=True)
def audit_log_delete_celery_task(self, payload: dict):
    AuditService.log_delete_sync(**payload)
