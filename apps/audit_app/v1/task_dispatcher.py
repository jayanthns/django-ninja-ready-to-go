from django.conf import settings

from common.logger_helper import get_logger_with_trace
from common.utils import normalize_value

USE_CELERY = getattr(settings, "AUDIT_USE_CELERY", False)
USE_DRAMATIQ = getattr(settings, "AUDIT_USE_DRAMATIQ", False)

if USE_CELERY:
    from .tasks import audit_log_create_celery_task as audit_log_create_task
    from .tasks import audit_log_delete_celery_task as audit_log_delete_task
    from .tasks import audit_log_update_celery_task as audit_log_update_task
elif USE_DRAMATIQ:
    from .tasks import audit_log_create_dramatiq_task as audit_log_create_task
    from .tasks import audit_log_delete_dramatiq_task as audit_log_delete_task
    from .tasks import audit_log_update_dramatiq_task as audit_log_update_task
else:
    # FALLBACK: No async backend → run inline
    audit_log_create_task = None
    audit_log_update_task = None
    audit_log_delete_task = None


class TaskDispatcher:
    """
    Unified async-dispatch interface for AuditService.
    Selects Celery / Dramatiq / inline automatically.
    """

    @staticmethod
    async def dispatch_create(payload: dict):
        logger = get_logger_with_trace(
            trace_id=payload.get("trace_id", ""), logger_name="audit_task_dispatcher::create"
        )
        payload.update({"changes": normalize_value(payload.get("changes", {}))})
        if audit_log_create_task:
            logger.info("Dispatching audit log create task asynchronously.")
            audit_log_create_task.delay(payload)
        else:
            from .services import AuditService

            logger.info("No async task backend configured; running audit log create inline.")
            await AuditService.log_create(**payload)

    @staticmethod
    async def dispatch_update(payload: dict):
        logger = get_logger_with_trace(
            trace_id=payload.get("trace_id", ""), logger_name="audit_task_dispatcher::update"
        )
        if audit_log_update_task:
            logger.info("Dispatching audit log update task asynchronously.")
            audit_log_update_task.delay(payload)
        else:
            from .services import AuditService

            logger.info("No async task backend configured; running audit log update inline.")
            await AuditService.log_update(**payload)

    @staticmethod
    async def dispatch_delete(payload: dict):
        logger = get_logger_with_trace(
            trace_id=payload.get("trace_id", ""), logger_name="audit_task_dispatcher::delete"
        )
        if audit_log_delete_task:
            logger.info("Dispatching audit log delete task asynchronously.")
            audit_log_delete_task.delay(payload)
        else:
            from .services import AuditService

            logger.info("No async task backend configured; running audit log delete inline.")
            await AuditService.log_delete(**payload)
