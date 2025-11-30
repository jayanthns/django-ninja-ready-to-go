from api_tests.client import APIClient


def run(client: APIClient):
    print("Running User Scenarios...")

    # 1. Register a user to get ID
    print("  - Registering user for retrieval...")
    register_payload = {
        "username": "test_user_get",
        "email": "test_user_get@example.com",
        "password": "password123",
    }
    resp = client.post("/api/v1/users/register", json=register_payload)
    assert resp.status_code == 200, f"Register failed: {resp.text}"
    user_id = resp.json()["data"]["id"]

    # 2. Get User
    print("  - Getting user...")
    resp = client.get(f"/api/v1/users/{user_id}/")
    assert resp.status_code == 200, f"Get user failed: {resp.text}"

    data = resp.json()
    from api_tests.assertions import assert_structure

    expected_user = {"id": str, "username": str, "email": str}
    expected_response = {"data": expected_user, "trace_id": str, "error": (dict, type(None))}
    assert_structure(data, expected_response, path="get_user_response")
    assert data["data"]["id"] == user_id
    assert data["data"]["email"] == "test_user_get@example.com"

    # Update/Delete/Me are not implemented in users_app views.

    print("User Scenarios Passed.")
