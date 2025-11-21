# Users App - User Management System

![Django](https://img.shields.io/badge/Django-4.2+-092E20?logo=django&logoColor=white) ![Django Ninja](https://img.shields.io/badge/Django%20Ninja-API-FF6B6B?logo=fastapi&logoColor=white) ![Async](https://img.shields.io/badge/Async-Enabled-00C7B7?logo=python&logoColor=white)

The **Users App** provides a comprehensive user management system with async support, secure password hashing, and RESTful API endpoints for user registration and retrieval.

## 🎯 Purpose & Features

### Core Functionality
- **User Registration**: Async user creation with automatic password hashing
- **User Retrieval**: Fetch user details by ID
- **Secure Passwords**: Built-in password hashing using Django's `make_password`
- **Email Validation**: Pydantic EmailStr validation
- **Async Operations**: Full async/await support for high performance

### Key Benefits
- **Production Ready**: Secure password handling and validation
- **Async Support**: Optimized database operations
- **Trace Integration**: Automatic request tracing
- **Type Safety**: Pydantic schemas with full type hints
- **Clean Architecture**: Service layer pattern for business logic

## 📁 App Structure

```
apps/users_app/
├── v1/
│   ├── __init__.py
│   ├── models.py         # User model with async password methods
│   ├── schemas.py        # Pydantic schemas for validation
│   ├── services.py       # Business logic layer
│   ├── views.py          # API endpoints
│   └── admin.py          # Django admin configuration
└── README.md             # This documentation
```

## 🗄️ Database Models

### User Model
Core user model with secure password handling.

```python
class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Hashed passwords
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    async def set_password(self, raw_password: str):
        """Asynchronously hash the password."""

    async def check_password(self, raw_password: str) -> bool:
        """Asynchronously verify password."""
```

**Fields:**
- `username`: Unique username (max 150 characters)
- `email`: Unique email address with validation
- `password`: Hashed password (never stores plain text)
- `created_at`: Timestamp of user creation
- `updated_at`: Timestamp of last update

**Methods:**
- `set_password()`: Async password hashing
- `check_password()`: Async password verification

## 🚀 API Endpoints

Base path: `/api/v1/users/`

### `POST /api/v1/users/register`
Register a new user with automatic password hashing.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": {}
}
```

**Notes:**
- Password is automatically hashed using Django's `make_password`
- Email must be valid format (validated by Pydantic)
- Username and email must be unique

---

### `GET /api/v1/users/{user_id}/`
Retrieve user details by ID.

**Path Parameters:**
- `user_id` (integer): User's unique identifier

**Response (200 OK):**
```json
{
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (404 Not Found):**
```json
{
  "error": {
    "message": "User not found"
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 📊 Pydantic Schemas

### UserSchema (Response)
```python
class UserSchema(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True  # Enables async model conversion
```

### UserCreateSchema (Request)
```python
class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    password: str  # Plain text (hashed before storage)
```

**Validation:**
- `email`: Must be valid email format
- `username`: Required string
- `password`: Required string (minimum length should be enforced in production)

## 🔧 Services Architecture

### UserService
Business logic layer for user operations.

**Methods:**

#### `create_user(payload: UserCreateSchema) -> UserSchema`
Creates a new user asynchronously with hashed password.

```python
user = await UserService.create_user(UserCreateSchema(
    username="johndoe",
    email="john@example.com",
    password="secure123"
))
```

**Process:**
1. Validates input using Pydantic schema
2. Hashes password with `make_password()`
3. Creates user in database asynchronously
4. Returns UserSchema

#### `get_user_by_id(user_id: int) -> UserSchema | None`
Retrieves a user by ID asynchronously.

```python
user = await UserService.get_user_by_id(1)
if user:
    print(f"Found user: {user.username}")
```

**Returns:**
- `UserSchema` if user exists
- `None` if user not found

## 🚀 Usage Examples

### Register a New User

```python
from apps.users_app.v1.schemas import UserCreateSchema
from apps.users_app.v1.services import UserService

# Create user
new_user = await UserService.create_user(
    UserCreateSchema(
        username="alice",
        email="alice@example.com",
        password="mySecurePassword"
    )
)

print(f"User created with ID: {new_user.id}")
# Password is securely hashed in database
```

### Fetch User by ID

```python
user = await UserService.get_user_by_id(1)

if user:
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
else:
    print("User not found")
```

### Password Verification (Model Method)

```python
from apps.users_app.v1.models import User

user = await User.objects.aget(id=1)

# Check password
is_valid = await user.check_password("mySecurePassword")
if is_valid:
    print("Password correct!")
```

## 🧪 Testing

Run user app tests:

```bash
# Run all user app tests
pytest tests/test_user_app/

# Run specific test files
pytest tests/test_user_app/test_user_views.py
pytest tests/test_user_app/test_user_services.py
pytest tests/test_user_app/test_user_models.py
```

### Test Coverage
- **UserService**: User creation and retrieval
- **User Model**: Password hashing and verification
- **API Endpoints**: Registration and user retrieval endpoints
- **Validation**: Schema validation and error handling

## 🔒 Security Features

### Password Security
- **Hashing**: All passwords hashed with Django's PBKDF2 algorithm
- **Never Plain Text**: Passwords never stored in plain text
- **Async Hashing**: Non-blocking password operations

### Input Validation
- **Email Validation**: Pydantic EmailStr ensures valid email format
- **Unique Constraints**: Username and email must be unique
- **Type Safety**: Pydantic schemas validate all inputs

### Best Practices
```python
# ✅ GOOD - Use service layer
user = await UserService.create_user(payload)

# ❌ BAD - Don't create users directly
user = await User.objects.acreate(
    password="plaintext"  # Not hashed!
)

# ✅ GOOD - Check password with model method
is_valid = await user.check_password(input_password)

# ❌ BAD - Don't compare passwords directly
if user.password == input_password:  # Never works (hashed!)
    ...
```

## 🔍 Django Admin Integration

The User model is automatically available in Django admin:
- View all users
- Search by username or email
- Filter by creation date
- Edit user details (note: password displayed as hash)

## 📈 Performance Considerations

### Async Operations
-All database operations use Django's async ORM (`acreate`, `aget`, `afirst`)
- Password hashing uses `sync_to_async` for Django's hashers
- Non-blocking operations for high concurrency

### Database Indexing
```python
# Recommended indexes (add to model)
class User(models.Model):
    username = models.CharField(max_length=150, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
```

## 🛠️ Configuration

### Django Settings

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    "apps.users_app.v1",
]

# Password hashers configuration
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]
```

### URL Configuration

```python
# In main urls.py
from apps.users_app.v1.views import router as users_router

api.add_router("/users/", users_router, tags=["Users"])
```

## 🚧 Future Enhancements

Potential improvements for this app:

1. **Authentication**:
   - JWT token generation
   - Login/logout endpoints
   - Session management

2. **User Profiles**:
   - Extended user information
   - Profile pictures
   - Bio and preferences

3. **Password Management**:
   - Password reset via email
   - Password change endpoint
   - Password strength validation

4. **User Permissions**:
   - Role-based access control
   - User groups
   - Permission management

5. **Email Verification**:
   - Email confirmation on registration
   - Verified email badge
   - Resend verification email

## 📚 Dependencies

### Core Dependencies
- `django`: Web framework
- `django-ninja`: API framework
- `pydantic`: Data validation with EmailStr
- `pydantic[email]`: Email validation support

### Password Hashing
- Uses Django's built-in `django.contrib.auth.hashers`
- PBKDF2 algorithm by default (secure and industry-standard)

## 🤝 Contributing

### Adding New Features

1. **Add Model Fields**: Update `models.py`
2. **Update Schemas**: Modify `schemas.py` for new fields
3. **Service Methods**: Add business logic in `services.py`
4. **API Endpoints**: Create views in `views.py`
5. **Tests**: Add test coverage

### Code Example: Adding a "Full Name" Field

```python
# models.py
class User(models.Model):
    # ... existing fields
    full_name = models.CharField(max_length=255, blank=True)

# schemas.py
class UserSchema(BaseModel):
    # ... existing fields
    full_name: str = ""

class UserCreateSchema(BaseModel):
    # ... existing fields
    full_name: str = ""
```

## 📄 API Testing

### Using cURL

```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "secure123"
  }'

# Get user by ID
curl http://localhost:8000/api/v1/users/1/
```

### Using Python requests

```python
import requests

# Register
response = requests.post(
    "http://localhost:8000/api/v1/users/register",
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "secure123"
    }
)
print(response.json())

# Get user
response = requests.get("http://localhost:8000/api/v1/users/1/")
print(response.json())
```

---

**Note**: This users app provides a foundation for user management. For production use, consider adding authentication, password validation rules, email verification, and comprehensive permission systems.
