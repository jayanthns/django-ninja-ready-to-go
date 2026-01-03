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

    data = resp.json()
    from api_tests.assertions import assert_structure

    expected_user = {"id": str, "username": str, "email": str, "is_verified": bool}
    expected_response = {"data": expected_user, "trace_id": str, "error": (dict, type(None))}
    assert_structure(data, expected_response, path="register_response")
    assert data["data"]["email"] == "test_auth@example.com"

    # Login/Refresh are not implemented in the current codebase, so we skip them.
    print("Auth Scenarios Passed.")
