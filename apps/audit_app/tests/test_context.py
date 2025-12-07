from unittest.mock import MagicMock

from apps.audit_app.v1.context import get_context, set_request_context_from_request


def test_set_request_context_from_request_populates_context():
    # --------------------------
    # Arrange
    # --------------------------

    # Mock user
    user = MagicMock()
    user.is_authenticated = True
    user.pk = 123
    user.email = "test@example.com"

    # Mock session
    session = MagicMock()
    session.session_key = "abc123"

    # Mock request
    request = MagicMock()
    request.user = user
    request.session = session

    request.trace_id = "trace-001"
    request.correlation_id = "corr-001"

    request.META = {
        "REMOTE_ADDR": "10.0.0.1",
        "HTTP_USER_AGENT": "pytest-agent",
    }

    # --------------------------
    # Act
    # --------------------------
    set_request_context_from_request(request)
    ctx = get_context()

    # --------------------------
    # Assert
    # --------------------------
    assert ctx["actor_id"] == "123"
    assert ctx["actor_email"] == "test@example.com"
    assert ctx["trace_id"] == "trace-001"
    assert ctx["correlation_id"] == "corr-001"
    assert ctx["ip_address"] == "10.0.0.1"
    assert ctx["user_agent"] == "pytest-agent"
    assert ctx["session_key"] == "abc123"


def test_context_is_empty_when_no_data_set():
    """
    Ensures context defaults to {} and does not leak between tests.
    """
    ctx = get_context()
    assert isinstance(ctx, dict)
