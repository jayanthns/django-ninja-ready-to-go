"""
Logger Helper System for Django requests and background tasks.

This module provides a centralized logging solution that automatically includes
trace ID and correlation ID context for every log message. It supports both
request-response contexts and background tasks/async code.
"""

import logging
import threading
from contextvars import ContextVar
from typing import Any, Dict, Optional

# Context variable to store the current logger adapter
_logger_context: ContextVar[Optional["LoggerAdapter"]] = ContextVar("logger_context", default=None)


class LoggerAdapter(logging.LoggerAdapter):
    """
    A logger adapter that automatically includes trace ID and correlation ID
    in all log messages. This is a singleton per request/task context.
    """

    def __init__(
        self, logger: logging.Logger, trace_id: str, correlation_id: Optional[str] = None, **context
    ):
        """
        Initialize the logger adapter.

        Args:
            logger: The base logger instance
            trace_id: The trace ID for this context
            correlation_id: The correlation ID if available
            **context: Additional context to include in all logs
        """
        super().__init__(logger, {})
        self.trace_id = trace_id
        self.correlation_id = correlation_id
        self.context = context.copy()
        self._lock = threading.Lock()

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process the log message and kwargs to include trace context.

        Args:
            msg: The log message
            kwargs: Additional keyword arguments

        Returns:
            Tuple of (processed_message, processed_kwargs)
        """
        # Add trace context to extra fields
        extra = kwargs.get("extra", {})
        extra.update({"trace_id": self.trace_id, "correlation_id": self.correlation_id, **self.context})
        kwargs["extra"] = extra

        return msg, kwargs

    def update_context(self, **context_updates: Any) -> None:
        """
        Update the context with new values.

        Args:
            **context_updates: Key-value pairs to update in the context
        """
        with self._lock:
            self.context.update(context_updates)

    def get_context(self) -> Dict[str, Any]:
        """
        Get a copy of the current context.

        Returns:
            Dictionary containing the current context
        """
        with self._lock:
            return {"trace_id": self.trace_id, "correlation_id": self.correlation_id, **self.context.copy()}


class LoggerHelper:
    """
    Helper class to manage logger adapters for requests and background tasks.
    """

    _instance: Optional["LoggerHelper"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LoggerHelper":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger helper."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._context_var = _logger_context

    def create_logger_adapter(
        self,
        trace_id: str,
        correlation_id: Optional[str] = None,
        logger_name: str = "request",
        **context: Any,
    ) -> LoggerAdapter:
        """
        Create a new logger adapter.

        Args:
            trace_id: Trace ID for this context
            correlation_id: Correlation ID if available
            logger_name: Name of the logger to use
            **context: Additional context to include

        Returns:
            LoggerAdapter instance
        """
        # Get the base logger
        base_logger = logging.getLogger(logger_name)

        # Create the adapter
        logger_adapter = LoggerAdapter(base_logger, trace_id, correlation_id, **context)

        # Store in context variable
        self._context_var.set(logger_adapter)

        return logger_adapter

    def get_current_logger(self) -> Optional[LoggerAdapter]:
        """
        Get the current logger adapter.

        Returns:
            LoggerAdapter if available, None otherwise
        """
        return self._context_var.get()

    def clear_logger(self) -> None:
        """Clear the current logger from context."""
        self._context_var.set(None)

    def get_logger_with_trace(
        self,
        trace_id: str,
        correlation_id: Optional[str] = None,
        logger_name: str = "request",
        **context: Any,
    ) -> LoggerAdapter:
        """
        Get or create a logger adapter with specific trace context.
        This is useful for background tasks or async code without request context.

        Args:
            trace_id: Trace ID for this context
            correlation_id: Correlation ID if available
            logger_name: Name of the logger to use
            **context: Additional context to include

        Returns:
            LoggerAdapter instance
        """
        # Check if we already have a logger with the same trace_id
        current_logger = self.get_current_logger()
        if current_logger and current_logger.trace_id == trace_id:
            # Update context if provided
            if context:  # pragma: no cover
                current_logger.update_context(**context)
            return current_logger

        # Create new logger adapter
        return self.create_logger_adapter(
            trace_id=trace_id, correlation_id=correlation_id, logger_name=logger_name, **context
        )


# Global instance
logger_helper = LoggerHelper()


def get_request_logger() -> Optional[LoggerAdapter]:
    """
    Get the current request logger adapter.

    Returns:
        LoggerAdapter if available, None otherwise
    """
    return logger_helper.get_current_logger()


def get_logger_with_trace(
    trace_id: str, correlation_id: Optional[str] = None, logger_name: str = "request", **context: Any
) -> LoggerAdapter:
    """
    Get or create a logger adapter with specific trace context.
    This is useful for background tasks or async code.

    Args:
        trace_id: Trace ID for this context
        correlation_id: Correlation ID if available
        logger_name: Name of the logger to use
        **context: Additional context to include

    Returns:
        LoggerAdapter instance
    """
    return logger_helper.get_logger_with_trace(
        trace_id=trace_id, correlation_id=correlation_id, logger_name=logger_name, **context
    )


def log_with_trace(
    logger: logging.Logger,
    level: int,
    msg: str,
    trace_id: str,
    correlation_id: Optional[str] = None,
    *args,
    **kwargs,
) -> None:
    """
    Log a message with automatic trace ID context.
    Falls back to regular logging if no logger adapter is available.

    Args:
        logger: The logger to use
        level: Log level
        msg: Log message
        trace_id: Trace ID to include
        correlation_id: Correlation ID to include
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments
    """
    # Add trace context to extra
    extra = kwargs.get("extra", {})
    extra.update({"trace_id": trace_id, "correlation_id": correlation_id})
    kwargs["extra"] = extra

    logger.log(level, msg, *args, **kwargs)
