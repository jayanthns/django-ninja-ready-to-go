import contextvars

_request_context = contextvars.ContextVar("audit_request_context", default={})


def set_request_context_from_request(request):
    user = getattr(request, "user", None)

    _request_context.set(
        {
            "actor_id": str(user.pk) if user and user.is_authenticated else None,
            "actor_email": getattr(user, "email", None) if user and user.is_authenticated else None,
            "trace_id": getattr(request, "trace_id", None),
            "correlation_id": getattr(request, "correlation_id", None),
            "ip_address": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT"),
            "session_key": getattr(getattr(request, "session", None), "session_key", None),
        }
    )


def get_context():
    return _request_context.get() or {}


def get_normalized_context():
    """
    Returns safe audit context.
    If called outside a request (shell, Celery worker), provides system defaults.
    """
    ctx = get_context() or {}

    # No request context? → System-level operation
    if not ctx.get("trace_id") and not ctx.get("actor_id"):
        return {
            "actor_id": "system",
            "actor_email": None,
            "trace_id": "system-trace",
            "correlation_id": None,
            "session_key": None,
            "ip_address": None,
            "user_agent": "shell",
        }

    return ctx
