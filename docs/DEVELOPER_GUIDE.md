# 🧑‍💻 Developer Guide

This guide provides naming conventions, coding standards, and best practices for contributing to this Django Ninja project.

## Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [Code Style & Standards](#code-style--standards)
3. [Project Structure](#project-structure)
4. [Best Practices](#best-practices)
5. [FAQ](#faq)

---

## Naming Conventions

### App Names

**Rule**: Use **plural nouns** with the `_app` suffix in snake_case.

**Pattern**: `{plural_noun}_app`

**Examples**:
- ✅ `animals_app` - manages multiple animals
- ✅ `users_app` - manages multiple users
- ✅ `products_app` - manages multiple products
- ✅ `orders_app` - manages multiple orders
- ❌ `animal_app` - singular (incorrect)
- ❌ `AnimalsApp` - PascalCase (incorrect)
- ❌ `animals-app` - kebab-case (incorrect)

**Rationale**:
- Plural nouns indicate the app manages a collection of entities
- The `_app` suffix clearly distinguishes apps from other modules
- Consistency across the codebase improves readability

**Special Cases**:
- For utility apps: `{function}_app` (e.g., `ping_app`, `auth_app`)
- For feature apps: `{feature}_app` (e.g., `notifications_app`, `payments_app`)

### Model Names

**Rule**: Use **singular nouns** in PascalCase.

**Pattern**: `{SingularNoun}`

**Examples**:
- ✅ `Animal` - represents a single animal
- ✅ `User` - represents a single user
- ✅ `Product` - represents a single product
- ✅ `OrderItem` - compound noun for related entities
- ❌ `Animals` - plural (incorrect)
- ❌ `animal` - lowercase (incorrect)

**Rationale**:
- Django convention: models represent single instances
- PascalCase follows Python class naming conventions (PEP 8)

### Schema Names

**Rule**: Use descriptive names with appropriate suffixes.

**Patterns**:
- Response schemas: `{Model}Schema`
- Create/input schemas: `{Model}CreateSchema` or `{Model}InputSchema`
- Update schemas: `{Model}UpdateSchema`
- Response wrappers: `{Model}ResponseSchema`

**Examples**:
```python
# Good
class AnimalSchema(Schema):          # For responses
    id: int
    name: str

class AnimalCreateSchema(Schema):   # For creation
    name: str

class AnimalUpdateSchema(Schema):   # For updates
    name: Optional[str]

class AnimalResponseSchema(Schema):  # API response wrapper
    data: Optional[AnimalSchema]
    trace_id: uuid.UUID
```

**Rationale**:
- Clear intent: immediately understand the schema's purpose
- Consistent suffixes make code predictable
- Follows Pydantic and API design best practices

### Service Names

**Rule**: Use `{Model}Service` pattern with PascalCase.

**Pattern**: `{Model}Service`

**Examples**:
- ✅ `AnimalService`
- ✅ `UserService`
- ✅ `ProductService`
- ❌ `AnimalServices` - plural (incorrect)
- ❌ `animal_service` - snake_case (incorrect)

**Rationale**:
- Clear separation of concerns (service layer pattern)
- Consistent with class naming conventions
- Easy to locate business logic

### View/Router Names

**Rule**: Use descriptive function names in snake_case for endpoints.

**Patterns**:
- List: `list_{plural_noun}`
- Retrieve: `get_{singular_noun}`
- Create: `create_{singular_noun}`
- Update: `update_{singular_noun}`
- Delete: `delete_{singular_noun}`

**Examples**:
```python
# Good
@router.get("/")
async def list_animals(request):
    """List all animals."""
    pass

@router.get("/{animal_id}/")
async def get_animal(request, animal_id: int):
    """Get a single animal."""
    pass

@router.post("/")
async def create_animal(request, payload: AnimalCreateSchema):
    """Create a new animal."""
    pass
```

**Rationale**:
- Function names follow PEP 8 (snake_case)
- Descriptive names improve code readability
- Consistent CRUD patterns across the codebase

### File Names

**Rule**: Use snake_case for all Python files.

**Standard Files**:
- `models.py` - Database models
- `schemas.py` - Pydantic schemas
- `services.py` - Business logic
- `views.py` - API endpoints
- `admin.py` - Django admin configuration
- `apps.py` - App configuration
- `tests.py` or `test_{feature}.py` - Tests

**Custom Files**:
- `utils.py` - Utility functions
- `constants.py` - Constants and enums
- `exceptions.py` - Custom exceptions
- `decorators.py` - Custom decorators

### Variable Names

**Rule**: Follow PEP 8 naming conventions.

**Patterns**:
- Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private variables: `_leading_underscore`
- Classes: `PascalCase`

**Examples**:
```python
# Good
user_count = 10
MAX_RETRY_ATTEMPTS = 3
_internal_cache = {}

class UserService:
    pass

# Bad
UserCount = 10  # Should be snake_case
maxRetryAttempts = 3  # Should be UPPER_SNAKE_CASE
```

---

## Code Style & Standards

### PEP 8 Compliance

This project follows [PEP 8](https://peps.python.org/pep-0008/) - the official Python style guide.

**Key Points**:
- **Indentation**: 4 spaces (no tabs)
- **Line Length**: Maximum 88 characters (Black formatter default)
- **Imports**: 
  - Standard library first
  - Third-party packages second
  - Local imports last
  - Alphabetically sorted within each group

**Example**:
```python
# Standard library
import uuid
from typing import List, Optional

# Third-party
from django.db import models
from ninja import Schema

# Local
from .models import Animal
from .schemas import AnimalCreateSchema
```

### Type Hints

**Rule**: Use type hints for all function signatures and class attributes.

**Examples**:
```python
# Good
async def get_animal(animal_id: int) -> Optional[Animal]:
    return await Animal.objects.filter(id=animal_id).afirst()

def calculate_total(items: List[int]) -> int:
    return sum(items)

# Bad
async def get_animal(animal_id):  # Missing type hints
    return await Animal.objects.filter(id=animal_id).afirst()
```

**Rationale**:
- Improves code readability
- Enables better IDE support
- Catches type errors early with mypy

### Async/Await

**Rule**: Use async/await for all database operations and I/O-bound tasks.

**Examples**:
```python
# Good - Async ORM operations
async def create_animal(name: str) -> Animal:
    return await Animal.objects.acreate(name=name)

async def list_animals() -> List[Animal]:
    return [animal async for animal in Animal.objects.all()]

# Bad - Sync operations (blocking)
def create_animal(name: str) -> Animal:
    return Animal.objects.create(name=name)
```

**Rationale**:
- Non-blocking operations improve performance
- Better scalability for concurrent requests
- Follows Django Ninja async best practices

### Docstrings

**Rule**: Use docstrings for all public functions, classes, and modules.

**Format**: Google-style docstrings

**Examples**:
```python
def create_animal(name: str, species: str, age: int) -> Animal:
    """Create a new animal instance.
    
    Args:
        name: The animal's name
        species: The animal's species
        age: The animal's age in years
        
    Returns:
        The created Animal instance
        
    Raises:
        ValidationError: If the data is invalid
    """
    pass
```

### Error Handling

**Rule**: Use specific exceptions and provide meaningful error messages.

**Examples**:
```python
# Good
try:
    animal = await AnimalService.get_animal(animal_id)
    if not animal:
        return 404, {"error": "Animal not found"}
except ValidationError as e:
    request.logger.error(f"Validation failed: {e}")
    return 400, {"error": str(e)}
except Exception as e:
    request.logger.exception("Unexpected error occurred")
    raise

# Bad
try:
    animal = await AnimalService.get_animal(animal_id)
except:  # Bare except
    pass  # Silent failure
```

---

## Project Structure

### App Organization

```
apps/
├── {app_name}/              # App root (plural noun + _app)
│   ├── __init__.py
│   └── v1/                  # Version 1
│       ├── __init__.py
│       ├── admin.py         # Django admin
│       ├── apps.py          # App config
│       ├── models.py        # Database models
│       ├── schemas.py       # Pydantic schemas
│       ├── services.py      # Business logic
│       ├── views.py         # API endpoints
│       └── tests.py         # Tests (optional)
```

### Versioning Strategy

**Rule**: Use versioned directories (v1, v2, etc.) for API evolution.

**Benefits**:
- Backward compatibility
- Gradual migration
- Clear API versioning

**Example**:
```python
# main/urls.py
from apps.animals_app.v1.views import router as animals_v1_router
from apps.animals_app.v2.views import router as animals_v2_router

api.add_router("/v1/animals/", animals_v1_router, tags=["Animals V1"])
api.add_router("/v2/animals/", animals_v2_router, tags=["Animals V2"])
```

---

## Best Practices

### 1. Service Layer Pattern

**Rule**: Keep business logic in services, not views.

```python
# Good - Logic in service
class AnimalService:
    @staticmethod
    async def create_animal(name: str, species: str) -> Animal:
        # Validation, business rules, etc.
        return await Animal.objects.acreate(name=name, species=species)

@router.post("/")
async def create_animal(request, payload: AnimalCreateSchema):
    animal = await AnimalService.create_animal(
        payload.name, 
        payload.species
    )
    return {"data": animal}

# Bad - Logic in view
@router.post("/")
async def create_animal(request, payload: AnimalCreateSchema):
    # Business logic mixed with HTTP handling
    animal = await Animal.objects.acreate(
        name=payload.name,
        species=payload.species
    )
    return {"data": animal}
```

### 2. Consistent Response Format

**Rule**: Use standardized response schemas across all endpoints.

```python
# Good - Consistent structure
{
    "data": {...},
    "trace_id": "uuid",
    "error": {}
}

# Use the helper
from common.base_schemas import create_api_response_schema

@router.get("/", response=create_api_response_schema(List[AnimalSchema]))
async def list_animals(request):
    return {
        "data": await AnimalService.list_animals(),
        "trace_id": str(request.trace_id),
        "error": {}
    }
```

### 3. Logging Best Practices

**Rule**: Use the request logger with contextual information.

```python
# Good
@router.post("/")
async def create_animal(request, payload: AnimalCreateSchema):
    request.logger.info(f"Creating animal: {payload.name}")
    
    try:
        animal = await AnimalService.create_animal(...)
        request.logger.info(f"Created animal with ID: {animal.id}")
        return {"data": animal}
    except Exception as e:
        request.logger.exception("Failed to create animal")
        raise
```

### 4. Database Optimization

**Rule**: Use select_related and prefetch_related to avoid N+1 queries.

```python
# Good - Optimized
animals = await Animal.objects.select_related('owner').all()

# Bad - N+1 queries
animals = await Animal.objects.all()
for animal in animals:
    owner = await animal.owner  # Separate query for each animal
```

### 5. Testing

**Rule**: Write tests for all critical functionality.

```python
# tests.py
import pytest
from .services import AnimalService

@pytest.mark.asyncio
async def test_create_animal():
    animal = await AnimalService.create_animal("Simba", "Lion", 5)
    assert animal.name == "Simba"
    assert animal.species == "Lion"
```

---

## FAQ

### General Questions

**Q: Should I use singular or plural for app names?**

A: Always use **plural nouns** for app names (e.g., `animals_app`, `users_app`). This indicates the app manages a collection of entities and follows the project convention.

**Q: When should I create a new app vs. adding to an existing one?**

A: Create a new app when:
- The functionality is logically separate (e.g., `payments_app` vs. `products_app`)
- It has its own set of models and business logic
- It could potentially be reused in other projects

Add to an existing app when:
- The functionality is closely related to existing features
- It shares the same models or domain logic

**Q: How do I name compound models?**

A: Use PascalCase without underscores:
- ✅ `OrderItem` (not `Order_Item`)
- ✅ `UserProfile` (not `User_Profile`)
- ✅ `ProductCategory` (not `Product_Category`)

### Naming Questions

**Q: What if my app manages a single entity (e.g., a settings page)?**

A: Use a descriptive plural or functional name:
- ✅ `settings_app` (functional)
- ✅ `configurations_app` (plural of configuration)
- ❌ `setting_app` (singular)

**Q: How do I name utility functions?**

A: Use descriptive snake_case names with verb prefixes:
- ✅ `calculate_total_price()`
- ✅ `format_date_string()`
- ✅ `validate_email_address()`
- ❌ `total()` (too vague)

**Q: Should service methods be static or instance methods?**

A: Use **static methods** for stateless operations (recommended):
```python
class AnimalService:
    @staticmethod
    async def create_animal(name: str) -> Animal:
        return await Animal.objects.acreate(name=name)
```

Use instance methods only if you need to maintain state.

### Code Style Questions

**Q: Should I use Black for formatting?**

A: Yes! Run `make black_format` before committing. Black is configured in `pyproject.toml` with:
- Line length: 88 characters
- Python version: 3.10+

**Q: How do I handle long import lines?**

A: Use parentheses for multi-line imports:
```python
from apps.animals_app.v1.schemas import (
    AnimalCreateSchema,
    AnimalSchema,
    AnimalUpdateSchema,
)
```

**Q: When should I use `Optional` vs. default values?**

A: Use `Optional` when a value can be `None`:
```python
# Good
def get_animal(animal_id: int) -> Optional[Animal]:
    pass

# For schemas with defaults
class AnimalSchema(Schema):
    name: str
    description: Optional[str] = None  # Can be None
```

### Async Questions

**Q: Should all views be async?**

A: Yes, for consistency and performance. Django Ninja supports async views natively.

**Q: Can I mix sync and async code?**

A: Avoid it when possible. If you must call sync code from async:
```python
from asgiref.sync import sync_to_async

@sync_to_async
def sync_function():
    pass

async def async_view():
    result = await sync_function()
```

**Q: How do I handle async list comprehensions?**

A: Use async for:
```python
# Good
animals = [animal async for animal in Animal.objects.all()]

# Bad
animals = [animal for animal in await Animal.objects.all()]  # Won't work
```

### Testing Questions

**Q: Where should I put tests?**

A: Options:
1. `apps/{app_name}/v1/tests.py` - Simple apps
2. `apps/{app_name}/v1/tests/` - Complex apps with multiple test files
3. `tests/test_{app_name}/` - Project root tests directory

**Q: How do I test async functions?**

A: Use `pytest-asyncio`:
```python
import pytest

@pytest.mark.asyncio
async def test_create_animal():
    animal = await AnimalService.create_animal("Simba", "Lion", 5)
    assert animal.name == "Simba"
```

### Django Admin Questions

**Q: Should I register all models in admin?**

A: Register models that need admin interface management:
```python
from django.contrib import admin
from .models import Animal

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'age', 'created_at')
    search_fields = ('name', 'species')
```

**Q: How do I customize admin for my app?**

A: Use `ModelAdmin` options:
- `list_display` - columns to show
- `list_filter` - sidebar filters
- `search_fields` - searchable fields
- `readonly_fields` - non-editable fields

### API Design Questions

**Q: Should I use `/api/v1/` or `/v1/api/`?**

A: Use `/api/v1/` (version after api):
```python
# Good
/api/v1/animals/
/api/v1/users/

# Bad
/v1/api/animals/
```

**Q: How do I handle pagination?**

A: Use query parameters:
```python
@router.get("/")
async def list_animals(request, page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size
    animals = await Animal.objects.all()[offset:offset + page_size]
    return {"data": animals, "page": page, "page_size": page_size}
```

**Q: Should I use PUT or PATCH for updates?**

A: 
- **PUT**: Full replacement (all fields required)
- **PATCH**: Partial update (only changed fields)

```python
# PUT - Replace entire resource
@router.put("/{id}/")
async def update_animal(request, id: int, payload: AnimalCreateSchema):
    pass

# PATCH - Update specific fields
@router.patch("/{id}/")
async def partial_update_animal(request, id: int, payload: AnimalUpdateSchema):
    pass
```

### Migration Questions

**Q: When should I create migrations?**

A: After any model changes:
```bash
make makemigrations
make migrate
```

**Q: How do I name custom migrations?**

A: Use descriptive names:
```bash
python manage.py makemigrations --name add_animal_weight_field
```

---

## Quick Reference

### Command Cheat Sheet

```bash
# Create new app
make create-app APP=products_app

# Code quality
make black_format      # Format code
make isort_format      # Sort imports
make flake8           # Lint code
make static-tests     # Run all checks

# Testing
make pytest           # Run tests

# Database
make makemigrations   # Create migrations
make migrate          # Apply migrations

# Development
make run              # Run dev server
make shell            # Django shell
```

### Naming Quick Reference

| Item | Pattern | Example |
|------|---------|---------|
| App | `{plural}_app` | `animals_app` |
| Model | `{Singular}` | `Animal` |
| Schema | `{Model}Schema` | `AnimalSchema` |
| Service | `{Model}Service` | `AnimalService` |
| View Function | `{verb}_{noun}` | `create_animal` |
| Variable | `snake_case` | `animal_count` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_ANIMALS` |
| Class | `PascalCase` | `AnimalService` |

---

## Additional Resources

- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Django Ninja Documentation](https://django-ninja.rest-framework.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Django Async Documentation](https://docs.djangoproject.com/en/stable/topics/async/)
- [Project Package Manager Guide](PACKAGE_MANAGER.md)
- [Project Testing Guide](TESTING.md)
- [App Generator Script Guide](../scripts/README.md)
