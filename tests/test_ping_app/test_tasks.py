from unittest.mock import patch

import pytest
from django.core.cache import cache

from apps.ping_app.v1.actors import ping_dramatiq_task
from apps.ping_app.v1.tasks import ping_celery_task


@pytest.mark.django_db
def test_ping_celery_task_execution():
    trace_id = "celery-unit-test-id"

    # Run task synchronously
    # Note: ping_celery_task is a bound task, so we need to call the underlying function
    # But since we are testing the logic inside, calling it directly works if we mock 'self' if needed.
    # However, Celery tasks are callable.

    # We need to mock time.sleep to avoid waiting
    with patch("time.sleep"):
        result = ping_celery_task(duration=1, trace_id=trace_id)

    assert result["message"] == "pong"
    assert result["service"] == "celery"

    # Check cache
    status = cache.get(f"task_status:{trace_id}")
    assert status["status"] == "SUCCESS"
    assert status["result"] == result


@pytest.mark.django_db
def test_ping_celery_task_failure():
    trace_id = "celery-fail-test-id"

    with patch("time.sleep", side_effect=Exception("Boom")):
        with pytest.raises(Exception):
            ping_celery_task(duration=1, trace_id=trace_id)

    # Check cache
    status = cache.get(f"task_status:{trace_id}")
    assert status["status"] == "FAILURE"
    assert "Boom" in status["error"]


@pytest.mark.django_db
def test_ping_dramatiq_task_execution():
    trace_id = "dramatiq-unit-test-id"

    with patch("time.sleep"):
        result = ping_dramatiq_task(duration=1, trace_id=trace_id)

    assert result["message"] == "pong"
    assert result["service"] == "dramatiq"

    # Check cache
    status = cache.get(f"task_status:{trace_id}")
    assert status["status"] == "SUCCESS"
    assert status["result"] == result


@pytest.mark.django_db
def test_ping_dramatiq_task_failure():
    trace_id = "dramatiq-fail-test-id"

    with patch("time.sleep", side_effect=Exception("Boom")):
        with pytest.raises(Exception):
            ping_dramatiq_task(duration=1, trace_id=trace_id)

    # Check cache
    status = cache.get(f"task_status:{trace_id}")
    assert status["status"] == "FAILURE"
    assert "Boom" in status["error"]


@pytest.mark.django_db
def test_ping_celery_task_no_trace_id():
    # Test execution without trace_id
    with patch("time.sleep"):
        result = ping_celery_task(duration=1, trace_id=None)

    assert result["message"] == "pong"
    assert result["service"] == "celery"
    # No cache check needed as trace_id is None


@pytest.mark.django_db
def test_ping_celery_task_failure_no_trace_id():
    # Test failure without trace_id
    with patch("time.sleep", side_effect=Exception("Boom")):
        with pytest.raises(Exception):
            ping_celery_task(duration=1, trace_id=None)


@pytest.mark.django_db
def test_ping_dramatiq_task_no_trace_id():
    # Test execution without trace_id
    with patch("time.sleep"):
        result = ping_dramatiq_task(duration=1, trace_id=None)

    assert result["message"] == "pong"
    assert result["service"] == "dramatiq"


@pytest.mark.django_db
def test_ping_dramatiq_task_failure_no_trace_id():
    # Test failure without trace_id
    with patch("time.sleep", side_effect=Exception("Boom")):
        with pytest.raises(Exception):
            ping_dramatiq_task(duration=1, trace_id=None)
