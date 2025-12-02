from unittest.mock import patch

import pytest

from apps.ping_app.v1.tasks import ping_celery_task, ping_dramatiq_task


class MockCache:
    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value, timeout=None):
        self._data[key] = value


@pytest.fixture
def mock_cache():
    c = MockCache()
    with (
        patch("apps.ping_app.v1.tasks.celery_tasks.cache", c),
        patch("apps.ping_app.v1.tasks.dramatiq_tasks.cache", c),
    ):
        yield c


def test_ping_celery_task_execution(mock_cache):
    trace_id = "celery-unit-test-id"

    # Run task synchronously
    # Note: ping_celery_task is a bound task, so we need to call the underlying function
    # But since we are testing the logic inside, calling it directly works if we mock 'self' if needed.
    # However, Celery tasks are callable.

    # We need to mock time.sleep to avoid waiting
    with patch("time.sleep"):
        result = ping_celery_task(duration=1, task_id=trace_id, trace_id=trace_id)

    assert result["message"] == "pong"
    assert result["service"] == "celery"

    # Check cache
    status = mock_cache.get(f"task_status:{trace_id}")
    assert status["status"] == "SUCCESS"
    assert status["result"] == result


def test_ping_celery_task_failure(mock_cache):
    trace_id = "celery-fail-test-id"

    with patch("time.sleep", side_effect=Exception("Boom")):
        with pytest.raises(Exception):
            ping_celery_task(duration=1, task_id=trace_id, trace_id=trace_id)

    # Check cache
    status = mock_cache.get(f"task_status:{trace_id}")
    assert status["status"] == "FAILURE"
    assert "Boom" in status["error"]


def test_ping_dramatiq_task_execution(mock_cache):
    trace_id = "dramatiq-unit-test-id"

    with patch("time.sleep"):
        result = ping_dramatiq_task(duration=1, trace_id=trace_id)

    assert result["message"] == "pong"
    assert result["service"] == "dramatiq"

    # Check cache
    status = mock_cache.get(f"task_status:{trace_id}")
    assert status["status"] == "SUCCESS"
    assert status["result"] == result


def test_ping_dramatiq_task_failure(mock_cache):
    trace_id = "dramatiq-fail-test-id"

    with patch("time.sleep", side_effect=Exception("Boom")):
        with pytest.raises(Exception):
            ping_dramatiq_task(duration=1, trace_id=trace_id)

    # Check cache
    status = mock_cache.get(f"task_status:{trace_id}")
    assert status["status"] == "FAILURE"
    assert "Boom" in status["error"]


def test_ping_celery_task_no_trace_id(mock_cache):
    # Test execution without trace_id
    with patch("time.sleep"):
        result = ping_celery_task(duration=1, trace_id=None)

    assert result["message"] == "pong"
    assert result["service"] == "celery"
    # No cache check needed as trace_id is None


def test_ping_celery_task_failure_no_trace_id(mock_cache):
    # Test failure without trace_id
    with patch("time.sleep", side_effect=Exception("Boom")):
        with pytest.raises(Exception):
            ping_celery_task(duration=1, trace_id=None)


def test_ping_dramatiq_task_no_trace_id(mock_cache):
    # Test execution without trace_id
    with patch("time.sleep"):
        result = ping_dramatiq_task(duration=1, trace_id=None)

    assert result["message"] == "pong"
    assert result["service"] == "dramatiq"


def test_ping_dramatiq_task_failure_no_trace_id(mock_cache):
    # Test failure without trace_id
    with patch("time.sleep", side_effect=Exception("Boom")):
        with pytest.raises(Exception):
            ping_dramatiq_task(duration=1, trace_id=None)
