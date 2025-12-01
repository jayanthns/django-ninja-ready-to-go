import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache

from apps.ping_app.v1.views.tasks_views import (
    get_celery_status,
    get_dramatiq_status,
    TaskTriggerSchema,
    trigger_celery_ping,
    trigger_dramatiq_ping,
)


@pytest.fixture
def mock_request():
    req = MagicMock()
    req.logger = MagicMock()
    return req


@pytest.mark.django_db
class TestTasksViews:

    @patch("apps.ping_app.v1.views.tasks_views.ping_celery_task.delay")
    def test_trigger_celery_ping(self, mock_delay, mock_request):
        payload = TaskTriggerSchema(duration=1)
        response = trigger_celery_ping(mock_request, payload)

        assert "task_id" in response
        assert response["status"] == "QUEUED"

        # Verify task called
        mock_delay.assert_called_once()
        args, kwargs = mock_delay.call_args
        assert kwargs["duration"] == 1
        assert kwargs["trace_id"] == response["task_id"]

        # Verify cache
        assert cache.get(f"task_status:{response['task_id']}") == "QUEUED"

    def test_get_celery_status_unknown(self, mock_request):
        task_id = str(uuid.uuid4())
        response = get_celery_status(mock_request, task_id)

        assert response["task_id"] == task_id
        assert response["status"] == "UNKNOWN"
        assert response["result"] is None

    def test_get_celery_status_queued(self, mock_request):
        task_id = str(uuid.uuid4())
        cache.set(f"task_status:{task_id}", "QUEUED")

        response = get_celery_status(mock_request, task_id)

        assert response["task_id"] == task_id
        assert response["status"] == "QUEUED"
        assert response["result"] is None

    def test_get_celery_status_success(self, mock_request):
        task_id = str(uuid.uuid4())
        result = {"message": "pong"}
        cache.set(f"task_status:{task_id}", {"status": "SUCCESS", "result": result})

        response = get_celery_status(mock_request, task_id)

        assert response["task_id"] == task_id
        assert response["status"] == "SUCCESS"
        assert response["result"] == result

    def test_get_celery_status_failure(self, mock_request):
        task_id = str(uuid.uuid4())
        error_msg = "Something went wrong"
        cache.set(f"task_status:{task_id}", {"status": "FAILURE", "error": error_msg})

        response = get_celery_status(mock_request, task_id)

        assert response["task_id"] == task_id
        assert response["status"] == "FAILURE"
        assert response["result"] == error_msg

    @patch("apps.ping_app.v1.views.tasks_views.ping_dramatiq_task.send")
    def test_trigger_dramatiq_ping(self, mock_send, mock_request):
        payload = TaskTriggerSchema(duration=1)
        response = trigger_dramatiq_ping(mock_request, payload)

        assert "task_id" in response
        assert response["status"] == "QUEUED"

        # Verify task called
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert kwargs["duration"] == 1
        assert kwargs["trace_id"] == response["task_id"]

        # Verify cache
        assert cache.get(f"task_status:{response['task_id']}") == "QUEUED"

    def test_get_dramatiq_status_unknown(self, mock_request):
        task_id = str(uuid.uuid4())
        response = get_dramatiq_status(mock_request, task_id)

        assert response["task_id"] == task_id
        assert response["status"] == "UNKNOWN"
        assert response["result"] is None

    def test_get_dramatiq_status_success(self, mock_request):
        task_id = str(uuid.uuid4())
        result = {"message": "pong"}
        cache.set(f"task_status:{task_id}", {"status": "SUCCESS", "result": result})

        response = get_dramatiq_status(mock_request, task_id)

        assert response["task_id"] == task_id
        assert response["status"] == "SUCCESS"
        assert response["result"] == result

    def test_get_dramatiq_status_queued(self, mock_request):
        task_id = str(uuid.uuid4())
        cache.set(f"task_status:{task_id}", "QUEUED")

        response = get_dramatiq_status(mock_request, task_id)

        assert response["task_id"] == task_id
        assert response["status"] == "QUEUED"
        assert response["result"] is None

    def test_get_dramatiq_status_failure(self, mock_request):
        task_id = str(uuid.uuid4())
        error_msg = "Something went wrong"
        cache.set(f"task_status:{task_id}", {"status": "FAILURE", "error": error_msg})

        response = get_dramatiq_status(mock_request, task_id)

        assert response["task_id"] == task_id
        assert response["status"] == "FAILURE"
        assert response["result"] == error_msg
