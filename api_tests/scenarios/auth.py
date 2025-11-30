from api_tests.client import APIClient


def run(client: APIClient):
    print("Running Auth Scenarios...")

    # 1. Register
    print("  - Registering new user...")
    register_payload = {
        "username": "test_auth_user",
        "email": "test_auth@example.com",
        "password": "password123",
    }
    # Note: URL is /api/v1/users/register based on users_app views
    resp = client.post("/api/v1/users/register", json=register_payload)
    assert resp.status_code == 200, f"Register failed: {resp.text}"
    data = resp.json()["data"]
    assert data["email"] == "test_auth@example.com"

    # Login/Refresh are not implemented in the current codebase, so we skip them.
    print("Auth Scenarios Passed.")
