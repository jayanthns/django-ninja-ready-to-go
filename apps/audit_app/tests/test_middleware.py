from unittest.mock import MagicMock, patch

import pytest

from apps.audit_app.v1.middleware import AuditContextMiddleware


@pytest.mark.asyncio
async def test_audit_context_middleware_calls_set_request_context():
    # Arrange ----------------------------------
    request = MagicMock()
    response = MagicMock()

    get_response = MagicMock(return_value=response)

    middleware = AuditContextMiddleware(get_response)

    # Patch set_request_context_from_request
    with patch("apps.audit_app.v1.middleware.set_request_context_from_request") as mocked_set_context:

        # Act ----------------------------------
        result = middleware(request)

        # Assert --------------------------------
        mocked_set_context.assert_called_once_with(request)
        get_response.assert_called_once_with(request)
        assert result is response
