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
    data = resp.json()
    assert data["data"]["email"] == "test_user_get@example.com"
    # user_id is available in data['data']['id'] if needed for future tests

    # 3. Duplicate Email Check
    print("  - Testing duplicate email registration...")
    duplicate_email_payload = {
        "username": "unique_username",
        "email": "test_user_get@example.com",  # Same email as above
        "password": "password123",
    }
    resp = client.post("/api/v1/users/register", json=duplicate_email_payload)
    assert resp.status_code == 400, f"Duplicate email should fail. Got: {resp.status_code}"
    error_data = resp.json()
    assert error_data["error"]["field"] == "email"
    assert "already registered" in error_data["error"]["message"]

    # 4. Duplicate Username Check
    print("  - Testing duplicate username registration...")
    duplicate_username_payload = {
        "username": "test_user_get",  # Same username as above
        "email": "unique_email@example.com",
        "password": "password123",
    }
    resp = client.post("/api/v1/users/register", json=duplicate_username_payload)
    assert resp.status_code == 400, f"Duplicate username should fail. Got: {resp.status_code}"
    error_data = resp.json()
    assert error_data["error"]["field"] == "username"
    assert "already exists" in error_data["error"]["message"]

    # 5. Invalid Email Check
    print("  - Testing invalid email registration...")
    invalid_email_payload = {
        "username": "invalid_email_user",
        "email": "not-an-email",
        "password": "password123",
    }
    resp = client.post("/api/v1/users/register", json=invalid_email_payload)
    assert resp.status_code == 422, f"Invalid email should fail validation. Got: {resp.status_code}"
    # Ninja/Pydantic validation error structure check
    error_data = resp.json()
    # It might be in detail or error.field depending on standard handler
    # Based on our previous fix, it returns standardized error
    if "error" in error_data and "field" in error_data["error"]:
        assert error_data["error"]["field"] == "email"
    else:
        # Fallback check if it's raw ninja error (though we standardized it)
        # Checking if 'email' is mentioned in the response text at least
        assert "email" in resp.text.lower()

    # Update/Delete/Me are not implemented in users_app views.

    print("User Scenarios Passed.")
