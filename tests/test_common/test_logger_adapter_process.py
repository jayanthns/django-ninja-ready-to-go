import logging

import pytest

from common.logger_helper import LoggerAdapter


def test_logger_adapter_process_adds_extra_and_preserves_existing():
    base_logger = logging.getLogger("test_logger")
    adapter = LoggerAdapter(
        base_logger, trace_id="tid-123", correlation_id="cid-456", custom_key="custom_val"
    )
    msg = "test message"
    kwargs = {"extra": {"original": "data"}}
    new_msg, new_kwargs = adapter.process(msg, kwargs)
    # Message should remain unchanged
    assert new_msg == msg
    # Extra should contain original plus trace info and custom context
    extra = new_kwargs.get("extra", {})
    assert extra["original"] == "data"
    assert extra["trace_id"] == "tid-123"
    assert extra["correlation_id"] == "cid-456"
    assert extra["custom_key"] == "custom_val"


def test_logger_adapter_process_creates_extra_when_missing():
    base_logger = logging.getLogger("test_logger2")
    adapter = LoggerAdapter(base_logger, trace_id="tid-789", correlation_id=None)
    msg = "another message"
    kwargs = {}
    new_msg, new_kwargs = adapter.process(msg, kwargs)
    assert new_msg == msg
    extra = new_kwargs.get("extra", {})
    assert extra["trace_id"] == "tid-789"
    assert extra["correlation_id"] is None
    # No other context should be present
    assert len(extra) == 2
