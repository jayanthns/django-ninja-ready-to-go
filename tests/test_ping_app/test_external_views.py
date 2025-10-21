import json
import uuid
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from apps.ping_app.v1.views.external_views import ping_external


@pytest.mark.asyncio
class TestExternalViewsPingExternal:

    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.logger = MagicMock()
        mock.trace_id = uuid.uuid4()
        return mock

    async def test_ping_external_success_response(self, mock_request):
        response = await ping_external(mock_request)

        response_json = json.loads(response.content)

        assert "data" in response_json
        assert "trace_id" in response_json
        assert "error" in response_json

        assert response_json["data"] == {"message": "external ping service ready", "status": "healthy"}
        assert response_json["trace_id"] == str(mock_request.trace_id)
        assert response_json["error"] == {}

        assert mock_request.logger.mock_calls == [call.info("Basic external ping endpoint accessed")]
