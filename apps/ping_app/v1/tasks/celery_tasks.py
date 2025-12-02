import logging
import time

from celery import shared_task
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue=settings.CELERY_QUEUE_NAME)
def ping_celery_task(self, duration: int = 0, task_id: str = None, trace_id: str = None) -> dict:
    """
    A simple Celery task that sleeps for a specified duration and returns a pong message.
    """
    if trace_id:
        logger.info(
            f"Task started | trace_id={trace_id} | task_id={task_id} | service=celery | duration={duration}"
        )
        cache.set(f"task_status:{task_id}", "RUNNING", timeout=300)

    try:
        time.sleep(duration)
        result = {"message": "pong", "service": "celery", "duration": duration}

        if trace_id:
            logger.info(f"Task success | trace_id={trace_id} | task_id={task_id} | service=celery")
            cache.set(f"task_status:{task_id}", {"status": "SUCCESS", "result": result}, timeout=300)

        return result
    except Exception as e:
        if trace_id:
            logger.error(
                f"Task failed | trace_id={trace_id} | task_id={task_id} | service=celery | error={str(e)}"
            )
            cache.set(f"task_status:{task_id}", {"status": "FAILURE", "error": str(e)}, timeout=300)
        raise e
