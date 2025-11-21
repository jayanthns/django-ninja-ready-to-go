import logging
from unittest.mock import MagicMock, patch

import pytest

from common.logger_helper import (
    debug_with_trace,
    error_with_trace,
    exception_with_trace,
    get_logger_with_trace,
    info_with_trace,
    log_with_trace,
    logger_helper,
    LoggerAdapter,
    warning_with_trace,
)


@pytest.fixture(autouse=True)
def clear_logger_context():
    """Ensure logger context is cleared before each test."""
    logger_helper.clear_logger()
    yield
    logger_helper.clear_logger()


def test_get_logger_with_trace_creates_adapter():
    trace_id = "trace-123"
    correlation_id = "corr-456"
    adapter = get_logger_with_trace(trace_id, correlation_id, logger_name="test_logger")
    # Should be a LoggerAdapter instance
    assert isinstance(adapter, LoggerAdapter)
    # Trace and correlation IDs should be set correctly
    assert adapter.trace_id == trace_id
    assert adapter.correlation_id == correlation_id
    # The adapter should be stored in the context
    assert logger_helper.get_current_logger() is adapter


def test_get_logger_with_trace_reuses_existing_adapter():
    trace_id = "trace-abc"
    adapter1 = get_logger_with_trace(trace_id, logger_name="test_logger")
    # Update context via second call with same trace_id and extra context
    adapter2 = get_logger_with_trace(trace_id, extra_key="extra_val")
    # Should return the same adapter instance
    assert adapter1 is adapter2
    # Context should be updated with extra_key
    assert adapter2.get_context()["extra_key"] == "extra_val"


def test_log_with_trace_calls_logger_log_with_extra():
    mock_logger = MagicMock(spec=logging.Logger)
    level = logging.INFO
    msg = "test message"
    trace_id = "tid"
    correlation_id = "cid"
    log_with_trace(mock_logger, level, msg, trace_id, correlation_id, extra={"foo": "bar"})
    # Verify logger.log called with correct args and extra containing trace info
    mock_logger.log.assert_called_once()
    called_args, called_kwargs = mock_logger.log.call_args
    assert called_args[0] == level
    assert called_args[1] == msg
    extra = called_kwargs.get("extra", {})
    assert extra["trace_id"] == trace_id
    assert extra["correlation_id"] == correlation_id
    # Original extra should be merged
    assert extra["foo"] == "bar"


def test_convenience_functions_delegate_to_log_with_trace():
    with patch("common.logger_helper.log_with_trace") as mock_log:
        logger = logging.getLogger("test")
        info_with_trace(logger, "info msg", "tid1")
        debug_with_trace(logger, "debug msg", "tid2")
        warning_with_trace(logger, "warn msg", "tid3")
        error_with_trace(logger, "error msg", "tid4")
        exception_with_trace(logger, "exc msg", "tid5")
        # Verify calls
        assert mock_log.call_count == 5
        calls = mock_log.call_args_list
        # info
        assert calls[0][0][1] == logging.INFO
        assert calls[0][0][2] == "info msg"
        # debug
        assert calls[1][0][1] == logging.DEBUG
        assert calls[1][0][2] == "debug msg"
        # warning
        assert calls[2][0][1] == logging.WARNING
        assert calls[2][0][2] == "warn msg"
        # error
        assert calls[3][0][1] == logging.ERROR
        assert calls[3][0][2] == "error msg"
        # exception should set exc_info=True in kwargs
        assert calls[4][1]["exc_info"] is True
        assert calls[4][0][1] == logging.ERROR
        assert calls[4][0][2] == "exc msg"
