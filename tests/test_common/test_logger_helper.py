import pytest

from common.logger_helper import LoggerAdapter, LoggerHelper
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


@pytest.mark.asyncio
class TestLoggerHelper:

    # --------------- Tests for LoggerHelper singleton behavior ---------------

    async def test_logger_helper_always_singleton_instance(self):
        helper1 = LoggerHelper()
        helper2 = LoggerHelper()
        assert helper1 is helper2

    # --------------- Tests for create_logger_adapter method ---------------

    async def test_create_logger_adapter_creates_instance_with_provided_params(self):
        helper = LoggerHelper()
        trace_id = "trace123"
        correlation_id = "corr456"
        logger_name = "test_logger"
        context = {"user_id": "user789"}

        logger_adapter = helper.create_logger_adapter(
            trace_id=trace_id,
            correlation_id=correlation_id,
            logger_name=logger_name,
            **context,
        )

        assert isinstance(logger_adapter, LoggerAdapter)
        assert logger_adapter.trace_id == trace_id
        assert logger_adapter.correlation_id == correlation_id
        assert logger_adapter.context["user_id"] == "user789"

    # --------------- Tests for get_current_logger method ---------------

    async def test_get_current_logger_returns_none_when_no_logger_set(self):
        helper = LoggerHelper()
        helper.clear_logger()  # Ensure no logger is set
        current_logger = helper.get_current_logger()
        assert current_logger is None

    async def test_get_current_logger_returns_set_logger_adapter(self):
        helper = LoggerHelper()
        trace_id = "trace123"

        logger_adapter = helper.create_logger_adapter(trace_id=trace_id)

        current_logger = helper.get_current_logger()
        assert current_logger is logger_adapter

    # --------------- Tests for clear_logger method ---------------
    async def test_clear_logger_removes_current_logger(self):
        helper = LoggerHelper()
        trace_id = "trace123"

        logger_adapter = helper.create_logger_adapter(trace_id=trace_id)

        # Ensure logger is set
        current_logger = helper.get_current_logger()
        assert current_logger is logger_adapter

        # Clear the logger
        helper.clear_logger()

        # Ensure logger is cleared
        current_logger = helper.get_current_logger()
        assert current_logger is None

    # --------------- Tests for get_logger_with_trace method ---------------
    async def test_get_logger_with_trace_returns_existing_logger_if_trace_id_matches(self):
        helper = LoggerHelper()
        trace_id = "trace123"
        context = {"user_id": "user789"}

        logger_adapter = helper.create_logger_adapter(trace_id=trace_id, **context)

        # Retrieve logger with same trace_id
        retrieved_logger = helper.get_logger_with_trace(trace_id=trace_id)

        assert retrieved_logger is logger_adapter

    async def test_get_logger_with_trace_creates_new_logger_if_trace_id_differs(self):
        helper = LoggerHelper()
        trace_id1 = "trace123"
        trace_id2 = "trace456"
        context1 = {"user_id": "user789"}
        context2 = {"user_id": "user000"}

        logger_adapter1 = helper.create_logger_adapter(trace_id=trace_id1, **context1)

        # Retrieve logger with different trace_id
        retrieved_logger = helper.get_logger_with_trace(trace_id=trace_id2, **context2)

        assert retrieved_logger is not logger_adapter1
        assert retrieved_logger.trace_id == trace_id2
        assert retrieved_logger.context["user_id"] == "user000"

    async def test_get_logger_with_trace_updates_context_of_existing_logger(self):
        helper = LoggerHelper()
        trace_id = "trace123"
        initial_context = {"user_id": "user789"}

        logger_adapter = helper.create_logger_adapter(trace_id=trace_id, **initial_context)

        # New context to update
        new_context = {"extra_id": "corr456"}

        # Retrieve logger with same trace_id but new context
        retrieved_logger = helper.get_logger_with_trace(trace_id=trace_id, **new_context)
        assert retrieved_logger is logger_adapter
        assert retrieved_logger.context["extra_id"] == "corr456"
