import time

import dramatiq
from django.conf import settings
from django.core.cache import cache


@dramatiq.actor(queue_name=settings.DRAMATIQ_QUEUE_NAME)
def ping_dramatiq_task(duration: int = 0, trace_id: str = None) -> dict:
    """
    A simple Dramatiq actor that sleeps for a specified duration and returns a pong message.
    """
    if trace_id:
        cache.set(f"task_status:{trace_id}", "RUNNING", timeout=300)

    try:
        time.sleep(duration)
        result = {"message": "pong", "service": "dramatiq", "duration": duration}

        if trace_id:
            cache.set(f"task_status:{trace_id}", {"status": "SUCCESS", "result": result}, timeout=300)

        return result
    except Exception as e:
        if trace_id:
            cache.set(f"task_status:{trace_id}", {"status": "FAILURE", "error": str(e)}, timeout=300)
        raise e
