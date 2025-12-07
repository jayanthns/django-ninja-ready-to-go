from .context import set_request_context_from_request


class AuditContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_request_context_from_request(request)
        return self.get_response(request)
