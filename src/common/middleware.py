import logging
import uuid
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse

# Configure logger for this module
logger = logging.getLogger(__name__)

# Trace ID header constants
TRACE_ID_HEADER = "HTTP_X_TRACE_ID"
TRACE_ID_RESPONSE_HEADER = "X-Trace-ID"
CORRELATION_ID_HEADER = "HTTP_X_CORRELATION_ID"
CORRELATION_ID_RESPONSE_HEADER = "X-Correlation-ID"


class TraceIDMiddleware:
    """
    Enhanced middleware to generate and attach trace IDs to each request.

    Features:
    - Generates unique trace IDs for each request
    - Supports external trace IDs from headers
    - Attaches trace ID to request object for easy access
    - Adds trace ID to response headers
    - Supports correlation IDs for distributed tracing
    - Integrates with Django logging
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and attach trace ID and correlation ID."""
        # Generate or extract trace ID
        trace_id = self._get_or_generate_trace_id(request)
        correlation_id = self._get_correlation_id(request)

        # Attach to request object
        request.trace_id = trace_id
        request.correlation_id = correlation_id

        # Log request with trace ID
        self._log_request(request, trace_id, correlation_id)

        # Process the request
        response = self.get_response(request)

        # Add trace headers to response
        response[TRACE_ID_RESPONSE_HEADER] = str(trace_id)
        if correlation_id:
            response[CORRELATION_ID_RESPONSE_HEADER] = str(correlation_id)

        # Log response with trace ID
        self._log_response(request, response, trace_id)

        return response

    def _get_or_generate_trace_id(self, request: HttpRequest) -> str:
        """
        Retrieve trace ID from headers or generate a new UUID.

        Args:
            request: The HTTP request object

        Returns:
            str: The trace ID for this request
        """
        # Check for existing trace ID in headers
        existing_trace_id = request.META.get(TRACE_ID_HEADER)
        if existing_trace_id:
            logger.debug(f"Using existing trace ID from header: {existing_trace_id}")
            return existing_trace_id

        # Generate new trace ID
        new_trace_id = str(uuid.uuid4())
        logger.debug(f"Generated new trace ID: {new_trace_id}")
        return new_trace_id

    def _get_correlation_id(self, request: HttpRequest) -> Optional[str]:
        """
        Retrieve correlation ID from headers if present.

        Args:
            request: The HTTP request object

        Returns:
            Optional[str]: The correlation ID if present, None otherwise
        """
        correlation_id = request.META.get(CORRELATION_ID_HEADER)
        if correlation_id:
            logger.debug(f"Using correlation ID from header: {correlation_id}")
        return correlation_id

    def _log_request(self, request: HttpRequest, trace_id: str, correlation_id: Optional[str]) -> None:
        """
        Log incoming request with trace information.

        Args:
            request: The HTTP request object
            trace_id: The trace ID for this request
            correlation_id: The correlation ID if present
        """
        extra_data = {
            "trace_id": trace_id,
            "method": request.method,
            "path": request.path,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "remote_addr": self._get_client_ip(request),
        }

        if correlation_id:
            extra_data["correlation_id"] = correlation_id

        logger.info(f"Request started - {request.method} {request.path}", extra=extra_data)

    def _log_response(self, request: HttpRequest, response: HttpResponse, trace_id: str) -> None:
        """
        Log response with trace information.

        Args:
            request: The HTTP request object
            response: The HTTP response object
            trace_id: The trace ID for this request
        """
        extra_data = {
            "trace_id": trace_id,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
        }

        logger.info(
            f"Request completed - {request.method} {request.path} - Status: {response.status_code}",
            extra=extra_data,
        )

    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Get the client IP address from the request.

        Args:
            request: The HTTP request object

        Returns:
            str: The client IP address
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip.strip()


class TraceIDContextFilter(logging.Filter):
    """
    Logging filter to automatically add trace ID to log records.
    This allows all log messages to include the trace ID without manual intervention.
    """

    def filter(self, record):
        """Add trace ID to log record if available."""
        # Try to get trace ID from the current request context
        try:
            from django.utils.deprecation import get_current_request

            request = get_current_request()
            if hasattr(request, "trace_id"):
                record.trace_id = str(request.trace_id)
                record.correlation_id = getattr(request, "correlation_id", None)
            else:
                record.trace_id = "no-trace-id"
                record.correlation_id = None
        except Exception:
            record.trace_id = "no-trace-id"
            record.correlation_id = None

        return True
