import pytest
from pydantic import ValidationError

from apps.users_app.v1.schemas import UserCreateSchema, UserSchema

# -------------------------------
# Tests for UserSchema
# -------------------------------


def test_user_schema_valid_data():
    data = {"id": 1, "username": "testuser", "email": "test@example.com"}
    user = UserSchema(**data)
    assert user.id == 1
    assert user.username == "testuser"
    assert user.email == "test@example.com"


def test_user_schema_invalid_email():
    data = {"id": 1, "username": "testuser", "email": "not-an-email"}
    with pytest.raises(ValidationError) as exc:
        UserSchema(**data)
    assert "value is not a valid email address" in str(exc.value)


def test_user_schema_missing_field():
    data = {"id": 1, "email": "test@example.com"}
    with pytest.raises(ValidationError) as exc:
        UserSchema(**data)
    assert "username" in str(exc.value)


# -------------------------------
# Tests for UserCreateSchema
# -------------------------------


def test_user_create_schema_valid():
    data = {"username": "newuser", "email": "new@example.com", "password": "secret123"}
    user = UserCreateSchema(**data)
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.password == "secret123"


def test_user_create_schema_missing_password():
    data = {
        "username": "newuser",
        "email": "new@example.com",
    }
    with pytest.raises(ValidationError) as exc:
        UserCreateSchema(**data)
    assert "password" in str(exc.value)


def test_user_create_schema_invalid_email():
    data = {"username": "newuser", "email": "invalid-email", "password": "secret123"}
    with pytest.raises(ValidationError) as exc:
        UserCreateSchema(**data)
    assert "value is not a valid email address" in str(exc.value)
