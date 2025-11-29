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
