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
