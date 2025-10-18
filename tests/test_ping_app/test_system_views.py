import pytest
from ninja import NinjaAPI
from ninja.testing import TestAsyncClient

# Import your router
from apps.ping_app.v1.views.system_views import router


@pytest.mark.asyncio
class TestSystemPing:
    @pytest.fixture(scope="session")
    def client(self):
        """
        Setup NinjaAPI client that includes your router.
        Equivalent to DRF's `APIClient()`, but async for Ninja.
        """
        api = NinjaAPI()
        api.add_router("/system", router)
        return TestAsyncClient(api)

    async def test_ping_endpoint_returns_pong(self, client):
        """✅ Should return pong and healthy response."""
        response = await client.get("/system/")

        # 1️⃣ Check status
        assert response.status_code == 200

        # 2️⃣ Check JSON structure
        data = response.json()
        assert "data" in data
        assert "trace_id" in data
        assert "error" in data

        # 3️⃣ Check response values
        assert data["data"]["message"] == "pong"
        assert data["data"]["status"] == "healthy"
        assert isinstance(data["trace_id"], str)
        assert data["error"] == {}

    async def test_ping_trace_id_is_unique_per_call(self, client):
        """✅ Each request should have a new trace_id value."""
        res1 = await client.get("/system/")
        res2 = await client.get("/system/")
        trace_id_1 = res1.json()["trace_id"]
        trace_id_2 = res2.json()["trace_id"]
        assert trace_id_1 != trace_id_2
