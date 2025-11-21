import pytest

from common.logger_helper import (
    get_logger_with_trace,
    get_request_logger,
    logger_helper,
    LoggerAdapter,
    LoggerHelper,
)


@pytest.fixture(autouse=True)
def reset_logger_helper():
    """Reset the singleton and context before each test."""
    # Reset the singleton instance and context variable
    LoggerHelper._instance = None
    # Ensure a fresh LoggerHelper is created
    helper = LoggerHelper()
    helper.clear_logger()
    yield
    # Cleanup after test
    helper.clear_logger()
    LoggerHelper._instance = None


def test_singleton_instance_is_same():
    first = LoggerHelper()
    second = LoggerHelper()
    assert first is second, "LoggerHelper should return the same singleton instance"


def test_init_runs_only_once():
    helper = LoggerHelper()
    # After first init, _initialized should be True
    assert getattr(helper, "_initialized", False) is True
    # Capture the current context var object
    context_before = helper._context_var
    # Call __init__ again by creating another instance (which is same)
    another = LoggerHelper()
    # Ensure the same context var is retained (no reinitialization)
    assert another._context_var is context_before


def test_get_logger_with_trace_creates_when_no_context():
    # Ensure no logger in context
    logger_helper.clear_logger()
    # No current logger should be present
    assert logger_helper.get_current_logger() is None
    # Call get_logger_with_trace, should create a new adapter
    trace_id = "trace-xyz"
    adapter = get_logger_with_trace(trace_id, logger_name="test_logger")
    assert isinstance(adapter, LoggerAdapter)
    # Now current logger should be set
    assert logger_helper.get_current_logger() is adapter
    assert adapter.trace_id == trace_id


def test_get_request_logger_behaviour():
    # When no logger is set, should return None
    logger_helper.clear_logger()
    assert get_request_logger() is None
    # Set a logger via get_logger_with_trace
    trace_id = "tid-123"
    adapter = get_logger_with_trace(trace_id, logger_name="test_logger")
    # get_request_logger should now return the same adapter
    assert get_request_logger() is adapter


def test_get_logger_with_trace_reuses_existing_adapter():
    # Create an adapter first
    trace_id = "reuse-123"
    adapter1 = get_logger_with_trace(trace_id, logger_name="test_logger")
    # Call again with same trace_id, should reuse
    adapter2 = get_logger_with_trace(trace_id, extra_key="extra")
    assert adapter1 is adapter2
    # Extra context should be added
    assert adapter2.get_context()["extra_key"] == "extra"


def test_get_logger_with_trace_creates_new_when_trace_mismatch():
    # Create initial logger with trace_id A
    adapter_a = get_logger_with_trace("trace-A", logger_name="test_logger")
    # Call with a different trace_id B, should create a new adapter
    adapter_b = get_logger_with_trace("trace-B", logger_name="test_logger")
    assert adapter_b is not adapter_a
    assert adapter_b.trace_id == "trace-B"
    # Ensure the current logger is now the new one
    assert logger_helper.get_current_logger() is adapter_b
