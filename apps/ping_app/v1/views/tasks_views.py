import uuid
from typing import Union

from django.core.cache import cache
from ninja import Router, Schema

from apps.ping_app.v1.actors import ping_dramatiq_task
from apps.ping_app.v1.tasks import ping_celery_task

router = Router()


class TaskTriggerSchema(Schema):
    duration: int = 0


class TaskResponseSchema(Schema):
    task_id: str
    status: str
    result: Union[dict, str] = None


@router.post("/celery/ping", response=TaskResponseSchema)
def trigger_celery_ping(request, payload: TaskTriggerSchema):
    """Trigger a Celery ping task."""
    trace_id = str(uuid.uuid4())
    cache.set(f"task_status:{trace_id}", "QUEUED", timeout=300)

    # Pass trace_id to the task
    ping_celery_task.delay(duration=payload.duration, trace_id=trace_id)

    # We return trace_id as task_id for consistency in status checking
    return {"task_id": trace_id, "status": "QUEUED"}


@router.get("/celery/status/{task_id}", response=TaskResponseSchema)
def get_celery_status(request, task_id: str):
    """Get the status of a Celery ping task."""
    status_data = cache.get(f"task_status:{task_id}")

    if status_data is None:
        return {"task_id": task_id, "status": "UNKNOWN", "result": None}

    if isinstance(status_data, dict):
        return {
            "task_id": task_id,
            "status": status_data.get("status"),
            "result": status_data.get("result") or status_data.get("error"),
        }

    return {"task_id": task_id, "status": status_data, "result": None}


@router.post("/dramatiq/ping", response=TaskResponseSchema)
def trigger_dramatiq_ping(request, payload: TaskTriggerSchema):
    """Trigger a Dramatiq ping task."""
    trace_id = str(uuid.uuid4())
    cache.set(f"task_status:{trace_id}", "QUEUED", timeout=300)

    # Pass trace_id to the task
    ping_dramatiq_task.send(duration=payload.duration, trace_id=trace_id)

    return {"task_id": trace_id, "status": "QUEUED"}


@router.get("/dramatiq/status/{task_id}", response=TaskResponseSchema)
def get_dramatiq_status(request, task_id: str):
    """Get the status of a Dramatiq ping task."""
    status_data = cache.get(f"task_status:{task_id}")

    if status_data is None:
        return {"task_id": task_id, "status": "UNKNOWN", "result": None}

    if isinstance(status_data, dict):
        return {
            "task_id": task_id,
            "status": status_data.get("status"),
            "result": status_data.get("result") or status_data.get("error"),
        }

    return {"task_id": task_id, "status": status_data, "result": None}
