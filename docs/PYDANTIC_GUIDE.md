# 🛡️ Pydantic & Django Ninja Development Guide

This guide provides industry best practices for writing Pydantic models (Schemas) within our Django Ninja project. It focuses on Pydantic V2 features, validation techniques, and integration patterns.

## Table of Contents

1. [Pydantic V2 Overview](#pydantic-v2-overview)
2. [Defining Schemas](#defining-schemas)
3. [Validation Methods](#validation-methods)
    - [Field Validators](#field-validators)
    - [Model Validators](#model-validators)
4. [Validation Modes: Before vs After](#validation-modes-before-vs-after)
5. [Best Practices](#best-practices)
6. [Django Ninja Integration](#django-ninja-integration)

---

## Pydantic V2 Overview

We use **Pydantic V2**, which offers significant performance improvements and a cleaner API compared to V1.

**Key Changes:**

- `validator` is replaced by `field_validator`.
- `root_validator` is replaced by `model_validator`.
- `BaseModel` methods like `dict()` are now `model_dump()`, and `json()` is `model_dump_json()`.

---

## Defining Schemas

In Django Ninja, Pydantic models are referred to as **Schemas**. They define the structure of request payloads and response data.

### Basic Schema

```python
from ninja import Schema
from pydantic import Field
from typing import Optional
from datetime import date

class UserCreateSchema(Schema):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    date_of_birth: Optional[date] = None
    is_active: bool = True
```

**Best Practice:**

- Use `ninja.Schema` instead of `pydantic.BaseModel` directly (Ninja's Schema inherits from BaseModel but adds Ninja-specific configuration).
- Use `Field(...)` to define constraints (length, regex, etc.) directly in the type definition for better OpenAPI documentation.

---

## Validation Methods

Pydantic V2 provides two main decorators for custom validation: `@field_validator` and `@model_validator`.

### Field Validators

Use `@field_validator` to validate **individual fields**.

```python
from pydantic import field_validator
from ninja import Schema

class ProductSchema(Schema):
    name: str
    price: float
    category: str

    @field_validator('name')
    @classmethod
    def name_must_be_capitalized(cls, v: str) -> str:
        if not v[0].isupper():
            raise ValueError('Name must start with a capital letter')
        return v.title()  # You can also transform the value

    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
```

### Model Validators

Use `@model_validator` to validate **multiple fields together** or the entire model state.

```python
from pydantic import model_validator
from ninja import Schema

class DateRangeSchema(Schema):
    start_date: str
    end_date: str

    @model_validator(mode='after')
    def check_date_order(self) -> 'DateRangeSchema':
        # In mode='after', 'self' is the model instance
        if self.start_date > self.end_date:
            raise ValueError('start_date must be before end_date')
        return self
```

---

## Validation Modes: Before vs After

Both validators support `mode='before'` and `mode='after'`. Understanding the difference is crucial.

### `mode='before'`

- **Runs BEFORE** Pydantic's internal parsing and validation.
- **Input:** Raw input data (dict, JSON, etc.).
- **Use Case:**
  - Pre-processing data to match the expected type.
  - Handling flexible input formats (e.g., accepting a comma-separated string for a list field).
  - Normalizing keys or values before type checking.

#### **Example: flexible list input**

```python
from typing import List
from pydantic import field_validator

class TagSchema(Schema):
    tags: List[str]

    @field_validator('tags', mode='before')
    @classmethod
    def split_string_tags(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',')]
        return v
```

### `mode='after'` (Default)

- **Runs AFTER** Pydantic's internal parsing and validation.
- **Input:** Validated python objects (e.g., `date` object, `int`, etc.).
- **Use Case:**
  - Business logic validation.
  - Cross-field validation (checking dependencies between fields).
  - Final data transformation.

#### **Example: Business logic check**

```python
@field_validator('age', mode='after')
@classmethod
def validate_age(cls, v: int) -> int:
    if v < 18:
        raise ValueError('Must be 18 or older')
    return v
```

---

## Best Practices

### 1. Separation of Concerns

- **Schemas (Pydantic):** Handle **data integrity**, **format**, and **structure** validation.
- **Services (Django):** Handle **business rules** involving database state (e.g., "does this user exist?", "is this email unique?").

**Don't do database queries in Pydantic validators.** It makes schemas hard to test and couples them to the DB.

**Bad:**

```python
# ❌ Avoid DB calls in schemas
@field_validator('email')
def validate_unique_email(cls, v):
    if User.objects.filter(email=v).exists():
        raise ValueError('Email exists')
    return v
```

**Good:**

```python
# ✅ Check uniqueness in the Service layer
# services.py
def create_user(payload: UserCreateSchema):
    if User.objects.filter(email=payload.email).exists():
        raise ValidationError("Email already exists")
    ...
```

### 2. Use `Field` for Simple Constraints

Don't write a custom validator for simple things like string length or regex. Use `Field()`.

```python
# ✅ Good
zip_code: str = Field(..., pattern=r"^\d{5}$")

# ❌ Unnecessary validator
@field_validator('zip_code')
def validate_zip(cls, v):
    if not re.match(r"^\d{5}$", v): ...
```

### 3. Explicit Error Messages

Pydantic generates good default errors, but custom `ValueError` messages should be user-friendly.

### 4. Use `Alias` for Frontend Compatibility

If your frontend sends `camelCase` but your python code uses `snake_case`, use `alias`.

```python
class UserSchema(Schema):
    first_name: str = Field(..., alias="firstName")
```

---

## Django Ninja Integration

### Schemas vs Models

- **Django Models:** Representation of your Database tables.
- **Pydantic Schemas:** Representation of your API Interface (Contract).

Always map between them explicitly or use `ModelSchema` (from `ninja`) if they are 1:1.

### Using `ModelSchema`

For simple CRUD, `ModelSchema` saves boilerplate.

```python
from ninja import ModelSchema
from .models import Animal

class AnimalSchema(ModelSchema):
    class Meta:
        model = Animal
        fields = ['id', 'name', 'species', 'age']
```

### Handling Nested Data

Use nested schemas to represent relationships.

```python
from typing import List

class AddressSchema(Schema):
    street: str
    city: str

class UserDetailSchema(Schema):
    name: str
    address: AddressSchema  # Nested schema
```

### Handling Lists of Nested Objects

To handle a list of objects, use `List[SchemaType]`.

```python
class OrderItemSchema(Schema):
    product_id: int
    quantity: int

class OrderCreateSchema(Schema):
    customer_id: int
    items: List[OrderItemSchema]  # List of nested objects
```

### Summary Table: When to use what?

| Requirement | Tool | Mode |
| :--- | :--- | :--- |
| **Type conversion** (str -> int) | Automatic (Pydantic) | N/A |
| **Simple constraints** (min_length, regex) | `Field(...)` | N/A |
| **Pre-processing raw input** (string -> list) | `@field_validator` | `mode='before'` |
| **Single field logic** (must be uppercase) | `@field_validator` | `mode='after'` |
| **Multi-field logic** (start < end) | `@model_validator` | `mode='after'` |
| **Database checks** (unique email) | **Service Layer** | N/A |

---

## Using Schemas in Views (DRF Comparison)

This section explains how to use Schemas in your views for input validation and response formatting, comparing it to Django Rest Framework (DRF) patterns.

### 1. Input Validation

**DRF:** You manually instantiate the serializer and call `is_valid()`.
**Ninja:** Validation is **automatic**. If you define a schema as an argument, Ninja validates it before calling your view.

```python
# DRF (Old way)
def create_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        validated_data = serializer.validated_data
        ...

# Ninja (New way)
@router.post("/users")
def create_user(request, payload: UserCreateSchema):
    # If code reaches here, 'payload' is already validated!
    # 'payload' is a Pydantic model instance, not a dict.
    pass
```

### 2. Accessing Validated Data

**DRF:** `serializer.validated_data` (returns a dict).
**Ninja:** The `payload` argument (returns a Pydantic object).

```python
# Ninja
def create_user(request, payload: UserCreateSchema):
    print(payload.username)  # Access attributes directly
    data = payload.model_dump()  # Convert to dict if needed
```

### 3. Saving Data (Model Mapping)

**DRF:** `serializer.save()` (handles object creation).
**Ninja:** You typically handle creation in a **Service** or directly in the view using the ORM. Pydantic schemas are decoupled from Models.

```python
# Ninja
def create_user(request, payload: UserCreateSchema):
    # Convert schema to dict and create model
    user = User.objects.create(**payload.model_dump())
    return user
```

### 4. Response Serialization

**DRF:** You manually serialize the instance: `UserSerializer(user).data`.
**Ninja:** You define the `response` schema in the decorator. Ninja automatically serializes the return value.

```python
# DRF (Old way)
return Response(UserSerializer(user).data)

# Ninja (New way)
@router.post("/users", response=UserSchema)
def create_user(request, payload: UserCreateSchema):
    user = User.objects.create(...)
    return user  # Ninja converts 'user' model instance to 'UserSchema' automatically
```

### 5. DRF vs Ninja Cheat Sheet

| Feature | DRF Pattern | Ninja Pattern |
| :--- | :--- | :--- |
| **Input Definition** | `Serializer(data=request.data)` | Function argument: `payload: Schema` |
| **Validation Trigger** | `serializer.is_valid(raise_exception=True)` | **Automatic** (before view execution) |
| **Access Data** | `serializer.validated_data['field']` | `payload.field` (Dot notation) |
| **To Dictionary** | `serializer.validated_data` | `payload.model_dump()` |
| **Object Creation** | `serializer.save()` | `Model.objects.create(**payload.model_dump())` |
| **Response Type** | `Response(Serializer(obj).data)` | `@router.get(..., response=Schema)` |
| **Partial Updates** | `Serializer(obj, data=..., partial=True)` | Use `Schema` with `Optional` fields (PATCH) |

---

## Execution Flow & Dependency Injection

Understanding the order of execution is critical when designing your API. Django Ninja uses a dependency injection system that resolves arguments before your view logic runs.

### Request Lifecycle

1. **Django Middleware**: Standard Django middleware runs first.
2. **Routing**: Ninja matches the URL to a view.
3. **Authentication**: If `auth=` is defined on the router or view, it runs **first**. If it fails, the view is never called.
4. **Dependency Resolution**: Ninja resolves all function arguments:
    - `request`: Injected automatically.
    - `payload`: Parsed and validated against the Schema.
    - `path parameters`: Parsed from the URL.
    - `query parameters`: Parsed from the query string.
5. **View Execution**: If all validation passes, your view function is called.

### Dependency Injection

Ninja automatically injects values based on type hints.

```python
@router.post("/items/{item_id}")
def create_item(
    request,                  # 1. Injected Request
    item_id: int,            # 2. Path Parameter (Validated)
    payload: ItemSchema,     # 3. Body Payload (Validated)
    filters: FilterSchema = Query(...) # 4. Query Params (Validated)
):
    # If code reaches here, EVERYTHING above is valid.
    pass
```

---

## Running Logic Before Validation

In DRF, you might be used to checking permissions or modifying `request.data` *before* passing it to the serializer. In Ninja, the flow is slightly different.

### 1. Authentication & Permissions (The "Gatekeeper")

Ninja's `auth` callbacks run **before** your view is called and **before** the schema validation is fully processed for the view logic (though basic type checking happens at the interface level).

Use this for:

- Checking if the user is logged in.
- Checking if the user is active.
- Checking API keys.

```python
# auth.py
def api_key_auth(request):
    if not request.headers.get("X-API-KEY"):
        return None  # Auth failed
    return "user_123"

# views.py
@router.post("/secure-data", auth=api_key_auth)
def create_secure_data(request, payload: DataSchema):
    # This code ONLY runs if api_key_auth returns a value.
    pass
```

### 2. Modifying Input Data

**DRF approach:** Modify `request.data` -> Serializer.
**Ninja approach:** Validate Payload -> Combine with Request Data -> Service.

In Ninja, you typically **don't** modify the raw input before validation. Instead, you accept the valid payload and then combine it with other data (like `request.user`) in your view or service.

#### **Example: Assigning an Owner to an Object**

```python
# Schema (Don't include owner_id here if it comes from the request!)
class ItemCreateSchema(Schema):
    name: str
    description: str

# View
@router.post("/items")
def create_item(request, payload: ItemCreateSchema):
    # 1. 'payload' is already validated (name, description)
    # 2. Get the user from the request (handled by auth)
    user = request.user
    
    # 3. Combine them in the service layer
    # We pass the payload AND the user separately
    return ItemService.create_item(payload, owner=user)
```

**Why?** This keeps your schemas pure and focused on the *client's* input, while your views/services handle the *context* (who is making the request).
