import pytest

from common.logger_helper import LoggerAdapter
from main.settings import logging


@pytest.mark.asyncio
class TestLoggerAdapter:

    # --------------- Tests for LoggerAdapter inheritance and instantiation ---------------

    async def test_logger_adapter_inherits_logger_methods(self):

        base_logger = logging.getLogger("test_logger")
        logger = LoggerAdapter(
            logger=base_logger,
            trace_id="trace123",
        )

        # Ensure that the logger adapter has the same methods as the base logger
        for method_name in ["debug", "info", "warning", "error", "critical"]:
            assert hasattr(logger, method_name)
            assert callable(getattr(logger, method_name))

    @pytest.mark.parametrize(
        "params",
        [
            {},
            {"correlation_id": "corr456"},
            {"user_id": "user789"},
            {"correlation_id": "corr456", "user_id": "user789"},
        ],
    )
    async def test_logger_adapter_missing_required_attributes_raises_error(self, params):
        with pytest.raises(TypeError):
            LoggerAdapter(logger=logging.getLogger("test_logger"), **params)

    # --------------- Tests for LoggerAdapter.process method ---------------

    async def test_process_on_valid_input_return_message_and_kwargs(self):

        logger = LoggerAdapter(
            logger=logging.getLogger("test_logger"),
            trace_id="trace123",
            correlation_id="corr456",
            user_id="user789",
        )

        msg, kwargs = logger.process("Test message", {})
        assert msg == "Test message"
        assert "extra" in kwargs
        assert kwargs["extra"]["trace_id"] == "trace123"
        assert kwargs["extra"]["correlation_id"] == "corr456"
        assert kwargs["extra"]["user_id"] == "user789"

    async def test_process_on_no_extra_in_kwargs_adds_extra(self):

        logger = LoggerAdapter(
            logger=logging.getLogger("test_logger"),
            trace_id="trace123",
        )

        msg, kwargs = logger.process("Another test message", {})
        assert msg == "Another test message"
        assert "extra" in kwargs
        assert kwargs["extra"]["trace_id"] == "trace123"

    async def test_process_on_existing_extra_merges_extra(self):

        logger = LoggerAdapter(
            logger=logging.getLogger("test_logger"),
            trace_id="trace123",
            user_id="user789",
        )

        existing_extra = {"session_id": "sess000"}
        msg, kwargs = logger.process("Message with existing extra", {"extra": existing_extra})
        assert msg == "Message with existing extra"
        assert "extra" in kwargs
        assert kwargs["extra"]["trace_id"] == "trace123"
        assert kwargs["extra"]["user_id"] == "user789"
        assert kwargs["extra"]["session_id"] == "sess000"

    # --------------- Tests for get_logger_with_trace function ---------------
    @pytest.mark.parametrize(
        "context",
        [
            {},
            {"user_id": "user789", "correlation_id": "corr456"},
        ],
    )
    async def test_update_context_method_update_with_new_context_passed(self, context):
        logger = LoggerAdapter(logger=logging.getLogger("test_logger"), trace_id="trace123", **context)

        logger = LoggerAdapter(
            logger=logging.getLogger("test_logger"),
            trace_id="trace123",
            correlation_id="corr456",
        )

        logger.update_context(user_id="user789", correlation_id="corr999")

        # Original logger should remain unchanged
        assert logger.trace_id == "trace123"
        assert logger.correlation_id == "corr456"
        assert logger.context["user_id"] == "user789"
        assert logger.context["correlation_id"] == "corr999"

    # --------------- Tests for get_context method ---------------

    async def test_get_context_method_returns_current_context(self):
        context = {"user_id": "user789", "correlation_id": "corr456"}
        logger = LoggerAdapter(
            logger=logging.getLogger("test_logger"),
            trace_id="trace123",
            **context,
        )

        current_context = logger.get_context()
        assert current_context["trace_id"] == "trace123"
        assert current_context["correlation_id"] == "corr456"
        assert current_context["user_id"] == "user789"
