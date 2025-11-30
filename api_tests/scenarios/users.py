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
    # Get user returns wrapped response: create_api_response_schema(UserSchema)
    # Checked views.py: return create_api_response_schema(UserSchema)(data=user, ...)
    data = resp.json()["data"]
    assert data["id"] == user_id
    assert data["email"] == "test_user_get@example.com"

    # Update/Delete/Me are not implemented in users_app views.

    print("User Scenarios Passed.")
