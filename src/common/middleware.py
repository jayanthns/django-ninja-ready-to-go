import uuid
from typing import Callable

from asgiref.sync import sync_to_async
from django.http import HttpRequest, HttpResponse
from django.utils.functional import SimpleLazyObject

TRACE_ID_HEADER = "HTTP_X_TRACE_ID"  # Custom trace ID header for external tracing


class TraceIDMiddleware:
    """ASGI Middleware to generate and attach a trace ID to each request."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and attach a trace ID."""
        request.trace_id = SimpleLazyObject(lambda: self.get_trace_id(request))
        response = self.get_response(request)
        response["X-Trace-ID"] = str(request.trace_id)
        return response

    def get_trace_id(self, request: HttpRequest) -> str:
        """Retrieve trace ID from headers or generate a new UUID."""
        return request.META.get(TRACE_ID_HEADER, str(uuid.uuid4()))
