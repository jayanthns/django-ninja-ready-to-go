import pytest
from django.test import Client


@pytest.mark.urls("main.urls")
def test_global_404_json_response(client: Client):
    """
    Test that accessing an unknown API route returns a JSON 404 response
    instead of the default Django HTML page.
    """
    response = client.get("/api/v1/unknown-endpoint-12345")

    assert response.status_code == 404
    assert "application/json" in response["Content-Type"]

    data = response.json()
    assert data["error"]["message"] == "Not Found"
    assert data["data"] is None
    # TraceIdMiddleware should have set this
    assert "trace_id" in data
    assert data["trace_id"] is not None
