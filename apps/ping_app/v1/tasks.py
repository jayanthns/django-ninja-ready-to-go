import time

from celery import shared_task
from django.core.cache import cache


@shared_task(bind=True)
def ping_celery_task(self, duration: int = 0, trace_id: str = None) -> dict:
    """
    A simple Celery task that sleeps for a specified duration and returns a pong message.
    """
    if trace_id:
        cache.set(f"task_status:{trace_id}", "RUNNING", timeout=300)

    try:
        time.sleep(duration)
        result = {"message": "pong", "service": "celery", "duration": duration}

        if trace_id:
            cache.set(f"task_status:{trace_id}", {"status": "SUCCESS", "result": result}, timeout=300)

        return result
    except Exception as e:
        if trace_id:
            cache.set(f"task_status:{trace_id}", {"status": "FAILURE", "error": str(e)}, timeout=300)
        raise e
