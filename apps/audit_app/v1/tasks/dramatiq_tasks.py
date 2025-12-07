import dramatiq

from apps.audit_app.v1.services import AuditService


@dramatiq.actor
def audit_log_create_dramatiq_task(payload: dict):
    return AuditService.log_create_sync(**payload)


@dramatiq.actor
def audit_log_update_dramatiq_task(payload: dict):
    return AuditService.log_update_sync(**payload)


@dramatiq.actor
def audit_log_delete_dramatiq_task(payload: dict):
    return AuditService.log_delete_sync(**payload)
