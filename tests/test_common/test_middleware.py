import json
import logging
import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpRequest, HttpResponse

from common.middleware import (
    CORRELATION_ID_RESPONSE_HEADER,
    TRACE_ID_RESPONSE_HEADER,
    TraceIDContextFilter,
    TraceIDMiddleware,
)


class TestTraceIDMiddleware:

    def _build_request(self, method="GET", path="/test", meta=None, user=None):
        request = HttpRequest()
        request.method = method
        request.path = path
        request.META = meta or {}
        if user:
            request.user = user
        return request

    def _dummy_get_response(self):
        return MagicMock(return_value=HttpResponse("OK", status=200))

    @patch("common.middleware.logger_helper.create_logger_adapter")
    @patch("common.middleware.logger_helper.clear_logger")
    def test_generates_new_trace_id(self, mock_clear_logger, mock_create_logger):
        middleware = TraceIDMiddleware(self._dummy_get_response())
        request = self._build_request()

        response = middleware(request)

        # Assert trace ID generated
        assert hasattr(request, "trace_id")
        uuid.UUID(request.trace_id)  # Validate UUID format

        # Response should contain trace ID header
        assert response[TRACE_ID_RESPONSE_HEADER] == request.trace_id

        # Logger cleanup called
        mock_clear_logger.assert_called_once()

        # Verify call arguments to ensure correct log message
        # We need to access the request.logger mock which was created by mocked_create_logger
        # But wait, create_logger_adapter returns the adapter.
        # The code does request.logger = logger_helper.create_logger_adapter(...)
        # So mocks are:
        # mock_create_logger -> returns Adapter Mock
        # request.logger -> Adapter Mock

        mock_adapter = mock_create_logger.return_value

        # [1] Request started
        args, _ = mock_adapter.info.call_args_list[0]
        assert "[1] Request started" in args[0]

        # [2] Request completed
        args, _ = mock_adapter.info.call_args_list[1]
        assert "[2] Request completed" in args[0]

    @patch("common.middleware.logger_helper.create_logger_adapter")
    def test_uses_existing_trace_id(self, mock_create_logger):
        existing_trace_id = "existing-trace-id"
        request = self._build_request(meta={"HTTP_X_TRACE_ID": existing_trace_id})
        middleware = TraceIDMiddleware(self._dummy_get_response())

        response = middleware(request)

        assert request.trace_id == existing_trace_id
        assert response[TRACE_ID_RESPONSE_HEADER] == existing_trace_id

    @patch("common.middleware.logger_helper.create_logger_adapter")
    def test_correlation_id_included(self, mock_create_logger):
        correlation_id = "corr-123"
        request = self._build_request(meta={"HTTP_X_CORRELATION_ID": correlation_id})
        middleware = TraceIDMiddleware(self._dummy_get_response())

        response = middleware(request)

        assert request.correlation_id == correlation_id
        assert response[CORRELATION_ID_RESPONSE_HEADER] == correlation_id

    @patch("common.middleware.logger_helper.create_logger_adapter")
    def test_logger_adapter_attached(self, mock_create_logger):
        middleware = TraceIDMiddleware(self._dummy_get_response())
        request = self._build_request()

        middleware(request)

        assert mock_create_logger.call_count >= 1
        assert hasattr(request, "logger")

    @patch("common.middleware.logger_helper.create_logger_adapter")
    @patch("common.middleware.logger_helper.clear_logger")
    def test_exception_flow(self, mock_clear_logger, mock_create_logger):
        def bad_response(request):
            raise ValueError("boom")

        middleware = TraceIDMiddleware(bad_response)
        request = self._build_request()

        with pytest.raises(ValueError):
            middleware(request)

        mock_clear_logger.assert_called_once()

        mock_adapter = mock_create_logger.return_value
        # [1] Request started
        args, _ = mock_adapter.info.call_args_list[0]
        assert "[1] Request started" in args[0]

        # [3] Request failed
        mock_adapter.exception.assert_called_once()
        args, _ = mock_adapter.exception.call_args
        assert "[3] Request failed" in args[0]

    def test_client_ip_forwarded(self):
        request = self._build_request(meta={"HTTP_X_FORWARDED_FOR": "10.1.2.3, 8.8.8.8"})
        middleware = TraceIDMiddleware(self._dummy_get_response())

        ip = middleware._get_client_ip(request)
        assert ip == "10.1.2.3"

    def test_client_ip_remote_addr(self):
        request = self._build_request(meta={"REMOTE_ADDR": "192.168.1.20"})
        middleware = TraceIDMiddleware(self._dummy_get_response())

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.20"

    @patch("common.middleware.logger_helper.create_logger_adapter")
    @patch("common.middleware.logger_helper.clear_logger")
    def test_response_contains_trace_id(self, mock_clear_logger, mock_create_logger):
        middleware = TraceIDMiddleware(self._dummy_get_response())
        request = self._build_request()

        response = middleware(request)

        assert TRACE_ID_RESPONSE_HEADER in response
        assert response[TRACE_ID_RESPONSE_HEADER] == request.trace_id

    def test_generic_500_post_passthrough(self):
        """
        Ensure that a generic 500 error on POST (not related to slash)
        passes through the middleware without being intercepted.
        """
        middleware = TraceIDMiddleware(self._dummy_get_response())
        # Mock get_response to return a 500 Generic Error
        middleware.get_response = MagicMock(return_value=HttpResponse("Generic Error", status=500))

        # Request with NO slash, so it falls through the first check
        # and response content "Generic Error" fails the second check.
        request = self._build_request(method="POST", path="/api/v1/test")

        response = middleware(request)

        # Should still be 500
        assert response.status_code == 500
        # Should contain trace ID (verifying it fell through to normal handling)
        assert TRACE_ID_RESPONSE_HEADER in response
        assert response.content == b"Generic Error"

    def test_500_post_with_slash_passthrough(self):
        """
        Ensure that a 500 error on POST where URL HAS a slash
        passes through, even if it looks like a RuntimeError.
        """
        middleware = TraceIDMiddleware(self._dummy_get_response())
        # Mock get_response to return a 500 with RuntimeError text (to simulate tricky case)
        middleware.get_response = MagicMock(
            return_value=HttpResponse("RuntimeError APPEND_SLASH", status=500)
        )

        # Request WITH slash, so the first check `not endswith(/)` is False.
        # It should short-circuit and pass through.
        request = self._build_request(method="POST", path="/api/v1/test/")

        response = middleware(request)

        # Should still be 500
        assert response.status_code == 500
        assert TRACE_ID_RESPONSE_HEADER in response
        assert response.content == b"RuntimeError APPEND_SLASH"

    def test_runtime_error_no_append_slash_passthrough(self):
        """
        Ensure that a 500 error on POST with 'RuntimeError' but MISSING 'APPEND_SLASH'
        passes through.
        """
        middleware = TraceIDMiddleware(self._dummy_get_response())
        # Mock 500 with RuntimeError but no mentions of APPEND_SLASH
        middleware.get_response = MagicMock(return_value=HttpResponse("RuntimeError occurred", status=500))

        # Request with NO slash. First check True.
        # Second check (RuntimeError) True.
        # Third check (APPEND_SLASH) False.
        request = self._build_request(method="POST", path="/api/v1/test")

        response = middleware(request)

        # Should still be 500
        assert response.status_code == 500
        assert TRACE_ID_RESPONSE_HEADER in response
        assert response.content == b"RuntimeError occurred"

    def test_runtime_error_exception_caught(self):
        """
        Ensure that if the RuntimeError BUbbles up (not caught downstream),
        we catch it in the except block and return 404.
        """

        def raising_response(request):
            raise RuntimeError("You called this URL via POST, but the URL doesn't end in a slash")

        middleware = TraceIDMiddleware(raising_response)

        request = self._build_request(method="POST", path="/api/v1/test")

        response = middleware(request)

        assert response.status_code == 404
        data = json.loads(response.content)
        assert "RuntimeError" in data["detail"]

    def test_500_post_intercepted_from_response(self):
        """
        Ensure that a 500 error on POST with missing slash AND valid RuntimeError text
        is intercepted and returns 404 JSON.
        """
        middleware = TraceIDMiddleware(self._dummy_get_response())
        # Mock get_response to return a 500 with the exact text looked for
        # Note: We need both 'RuntimeError' and 'APPEND_SLASH' in the content
        content = b"Traceback... RuntimeError ... You called this URL via POST ... APPEND_SLASH"
        middleware.get_response = MagicMock(return_value=HttpResponse(content, status=500))

        request = self._build_request(method="POST", path="/api/v1/test")  # No trailing slash

        response = middleware(request)

        # Should be intercepted and converted to 404
        assert response.status_code == 404
        assert TRACE_ID_RESPONSE_HEADER in response

        data = json.loads(response.content)
        assert "RuntimeError" in data["detail"]
        assert "Please add a trailing slash" in data["detail"]


class TestTraceIDContextFilter:

    def setup_method(self):
        self.filter = TraceIDContextFilter()
        self.record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )

    @patch("common.middleware.get_request_logger")
    def test_filter_with_request_logger(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_logger.trace_id = "trace-123"
        mock_logger.correlation_id = "corr-456"
        mock_get_logger.return_value = mock_logger

        result = self.filter.filter(self.record)

        assert result is True
        assert self.record.trace_id == "trace-123"
        assert self.record.correlation_id == "corr-456"

    @patch("common.middleware.get_request_logger")
    def test_filter_no_request_logger(self, mock_get_logger):
        mock_get_logger.return_value = None

        result = self.filter.filter(self.record)

        assert result is True
        assert self.record.trace_id == "no-trace-id"
        assert self.record.correlation_id is None

    @patch("common.middleware.get_request_logger")
    def test_filter_exception_in_logger(self, mock_get_logger):
        mock_get_logger.side_effect = Exception("boom")

        result = self.filter.filter(self.record)

        assert result is True
        assert self.record.trace_id == "no-trace-id"
        assert self.record.correlation_id is None

    def test_filter_always_returns_true(self):
        # Even if record doesn't have attributes initially
        result = self.filter.filter(self.record)
        assert result is True
