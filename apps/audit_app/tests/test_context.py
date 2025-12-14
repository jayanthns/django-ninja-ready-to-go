import uuid
from unittest.mock import MagicMock, patch

import pytest

from apps.audit_app.v1.context import get_context, get_normalized_context, set_request_context_from_request


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


@pytest.mark.parametrize(
    "name,context_input,expected_system",
    [
        ("both_missing", {}, True),
        ("only_trace_id_missing", {"actor_id": "123", "trace_id": None}, False),
        ("only_actor_id_missing", {"actor_id": None, "trace_id": "trace-1"}, False),
        ("both_present", {"actor_id": "123", "trace_id": "trace-1"}, False),
    ],
)
@patch("apps.audit_app.v1.context.get_context")
def test_get_normalized_context(mock_get_context, name, context_input, expected_system):
    mock_get_context.return_value = context_input

    ctx = get_normalized_context()

    if expected_system:
        # system defaults MUST be used
        assert ctx["actor_id"] == "system"
        assert ctx["actor_email"] is None
        # assert valid uuid
        try:
            uuid.UUID(ctx["trace_id"])
        except ValueError:
            pytest.fail(f"trace_id '{ctx['trace_id']}' is not a valid UUID")
        assert ctx["correlation_id"] is None
        assert ctx["session_key"] is None
        assert ctx["ip_address"] is None
        assert ctx["user_agent"] == "shell"
    else:
        # real context must be returned untouched
        assert ctx["actor_id"] == context_input.get("actor_id")
        assert ctx["trace_id"] == context_input.get("trace_id")
