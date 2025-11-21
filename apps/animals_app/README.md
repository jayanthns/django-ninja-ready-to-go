# Animals App - CRUD Operations Demo

![Django](https://img.shields.io/badge/Django-4.2+-092E20?logo=django&logoColor=white) ![Django Ninja](https://img.shields.io/badge/Django%20Ninja-API-FF6B6B?logo=fastapi&logoColor=white) ![Async](https://img.shields.io/badge/Async-Enabled-00C7B7?logo=python&logoColor=white)

The **Animals App** demonstrates complete CRUD (Create, Read, Update, Delete) operations with Django Ninja, showcasing async database operations, contextual logging, and RESTful API best practices.

## 🎯 Purpose & Features

### Core Functionality
- **Full CRUD**: Complete Create, Read, Update, Delete operations
- **Async Operations**: All endpoints use async/await for performance
- **Contextual Logging**: Integrated with trace_id for request tracking
- **List & Detail Views**: Browse all animals or fetch specific ones
- **Logger Demo**: Example endpoint showcasing logging capabilities

### Key Benefits
- **Learning Resource**: Perfect example of Django Ninja CRUD patterns
- **Production Patterns**: Demonstrates service layer, schemas, and async ORM
- **Logging Integration**: Shows how to use request.logger effectively
- **Type Safety**: Full Pydantic validation and type hints

## 📁 App Structure

```
apps/animals_app/
├── v1/
│   ├── __init__.py
│   ├── models.py         # Animal model
│   ├── schemas.py        # Pydantic schemas for validation
│   ├── services.py       # Business logic layer (CRUD operations)
│   ├── views.py          # API endpoints
│   └── admin.py          # Django admin configuration
└── README.md             # This documentation
```

## 🗄️ Database Models

### Animal Model
Simple model demonstrating core Django ORM patterns.

```python
class Animal(models.Model):
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    age = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
```

**Fields:**
- `name`: Animal's name (e.g., "Simba", "Dumbo")
- `species`: Species type (e.g., "Lion", "Elephant")
- `age`: Age in years
- `created_at`: Timestamp of when animal was added

## 🚀 API Endpoints

Base path: `/api/v1/animals/`

### `POST /api/v1/animals/`
Create a new animal.

**Request Body:**
```json
{
  "name": "Simba",
  "species": "Lion",
  "age": 5
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": 1,
    "name": "Simba",
    "species": "Lion",
    "age": 5
  },
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": {}
}
```

**Logging:**
```
INFO: Creating new animal: Simba (Lion) [trace_id=550e8400...]
INFO: Successfully created animal with ID: 1 [trace_id=550e8400...]
```

---

### `GET /api/v1/animals/`
List all animals.

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Simba",
      "species": "Lion",
      "age": 5
    },
    {
      "id": 2,
      "name": "Dumbo",
      "species": "Elephant",
      "age": 3
    }
  ],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": {}
}
```

---

### `GET /api/v1/animals/{animal_id}/`
Get a single animal by ID.

**Path Parameters:**
- `animal_id` (integer): Animal's unique identifier

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Simba",
  "species": "Lion",
  "age": 5
}
```

**Response (404 Not Found):**
```json
{
  "error": "Animal not found"
}
```

---

### `PUT /api/v1/animals/{animal_id}/`
Update an existing animal.

**Request Body:**
```json
{
  "name": "Simba",
  "species": "Lion",
  "age": 6
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Simba",
  "species": "Lion",
  "age": 6
}
```

**Response (404 Not Found):**
```json
{
  "error": "Animal not found"
}
```

---

### `DELETE /api/v1/animals/{animal_id}/`
Delete an animal.

**Response (200 OK):**
```json
{
  "message": "Animal deleted successfully"
}
```

**Response (404 Not Found):**
```json
{
  "error": "Animal not found"
}
```

**Logging:**
```
INFO: Attempting to delete animal with ID: 1 [trace_id=550e8400...]
INFO: Successfully deleted animal with ID: 1 [trace_id=550e8400...]
```

---

### `GET /api/v1/animals/logger-demo/`
Demo endpoint showcasing the logging system.

**Response (200 OK):**
```json
{
  "message": "Logger helper demo completed successfully!",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "req-abc123",
  "current_context": {
    "trace_id": "550e8400...",
    "correlation_id": "req-abc123",
    "demo_step": "context_update",
    "custom_field": "custom_value"
  },
  "request_info": {
    "method": "GET",
    "path": "/api/v1/animals/logger-demo/",
    "user_agent": "Mozilla/5.0..."
  }
}
```

**Logging Output:**
```
DEBUG: This is a debug message
INFO: This is an info message
WARNING: This is a warning message
INFO: This message includes updated context [demo_step=context_update,custom_field=custom_value]
INFO: Operation completed successfully: 42
```

## 📊 Pydantic Schemas

### AnimalSchema (Response)
```python
class AnimalSchema(Schema):
    id: int
    name: str
    species: str
    age: int
```

### AnimalCreateSchema (Request)
```python
class AnimalCreateSchema(Schema):
    name: str
    species: str
    age: int
```

### AnimalResponseSchema (Full Response)
```python
class AnimalResponseSchema(Schema):
    data: Optional[AnimalSchema] = None
    error: Optional[dict] = None
    trace_id: uuid.UUID
```

## 🔧 Services Architecture

### AnimalService
Handles all business logic for animal management.

**Methods:**

#### `create_animal(name: str, species: str, age: int) -> Animal`
Creates a new animal asynchronously.

```python
animal = await AnimalService.create_animal("Simba", "Lion", 5)
print(f"Created: {animal.name}")
```

#### `list_animals() -> List[Animal]`
Retrieves all animals asynchronously.

```python
animals = await AnimalService.list_animals()
for animal in animals:
    print(animal.name)
```

#### `get_animal(animal_id: int) -> Optional[Animal]`
Fetches a single animal by ID.

```python
animal = await AnimalService.get_animal(1)
if animal:
    print(f"Found: {animal.name}")
```

#### `update_animal(animal_id: int, data: AnimalCreateSchema) -> Optional[Animal]`
Updates an existing animal.

```python
updated = await AnimalService.update_animal(
    1,
    AnimalCreateSchema(name="Simba", species="Lion", age=6)
)
```

#### `delete_animal(animal_id: int) -> bool`
Deletes an animal and returns success status.

```python
success = await AnimalService.delete_animal(1)
if success:
    print("Animal deleted!")
```

## 🚀 Usage Examples

### Complete CRUD Workflow

```python
from apps.animals_app.v1.schemas import AnimalCreateSchema
from apps.animals_app.v1.services import AnimalService

# Create
animal = await AnimalService.create_animal("Simba", "Lion", 5)
print(f"Created animal with ID: {animal.id}")

# Read (List All)
all_animals = await AnimalService.list_animals()
print(f"Total animals: {len(all_animals)}")

# Read (Single)
animal = await AnimalService.get_animal(1)
print(f"Animal: {animal.name}, Age: {animal.age}")

# Update
updated_animal = await AnimalService.update_animal(
    1,
    AnimalCreateSchema(name="Simba", species="Lion", age=6)
)
print(f"Updated age to: {updated_animal.age}")

# Delete
deleted = await AnimalService.delete_animal(1)
print(f"Deleted: {deleted}")  # True or False
```

### Using with Request Logger

```python
# In views.py
@router.post("/")
async def create_animal(request, payload: AnimalCreateSchema):
    # Log with automatic trace_id
    request.logger.info(f"Creating animal: {payload.name}")

    try:
        animal = await AnimalService.create_animal(
            payload.name,
            payload.species,
            payload.age
        )
        request.logger.info(f"Created successfully: {animal.id}")
        return {"data": animal, "trace_id": str(request.trace_id)}

    except Exception as e:
        request.logger.exception(f"Failed to create animal")
        raise
```

## 🧪 Testing

Run animal app tests:

```bash
# Run all animal app tests
pytest tests/test_animals_app/

# Run with coverage
pytest tests/test_animals_app/ --cov=apps.animals_app
```

### Test Scenarios
- ✅ Create animal with valid data
- ✅ List all animals
- ✅ Get specific animal by ID
- ✅ Update animal details
- ✅ Delete animal
- ✅ Handle non-existent animal (404 responses)
- ✅ Validate input schemas

## 🔍 Django Admin Integration

The Animal model is available in Django admin:

```python
# admin.py
from django.contrib import admin
from .models import Animal

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'age', 'created_at')
    list_filter = ('species', 'age')
    search_fields = ('name', 'species')
    readonly_fields = ('created_at',)
```

**Features:**
- List view with all fields
- Filter by species and age
- Search by name or species
- Read-only created timestamp

## 📈 Performance Considerations

### Async Operations
- All database queries use Django's async ORM
- `acreate`, `aupdate`, `adelete`, `aget`, `afirst`
- List comprehension with `async for`

### Database Optimization
```python
# Efficient bulk operations
animals = [animal async for animal in Animal.objects.all()]

# Use select_related / prefetch_related for relations
animals = await Animal.objects.select_related('owner').all()
```

## 🔍 Logging Best Practices

This app demonstrates proper logging patterns:

### Basic Logging
```python
request.logger.info("Normal operation")
request.logger.warning("Something unusual")
request.logger.error("Something failed")
```

### Contextual Logging
```python
# Update context for all subsequent logs
request.logger.update_context(
    operation="create_animal",
    animal_name=payload.name
)

request.logger.info("Creating animal")  # Includes context
```

### Exception Logging
```python
try:
    result = await risky_operation()
except Exception:
    request.logger.exception("Operation failed")  # Includes traceback
    raise
```

## 📚 API Testing Examples

### Using cURL

```bash
# Create animal
curl -X POST http://localhost:8000/api/v1/animals/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Simba", "species": "Lion", "age": 5}'

# List all animals
curl http://localhost:8000/api/v1/animals/

# Get specific animal
curl http://localhost:8000/api/v1/animals/1/

# Update animal
curl -X PUT http://localhost:8000/api/v1/animals/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Simba", "species": "Lion", "age": 6}'

# Delete animal
curl -X DELETE http://localhost:8000/api/v1/animals/1/

# Logger demo
curl http://localhost:8000/api/v1/animals/logger-demo/
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/animals"

# Create
response = requests.post(
    BASE_URL + "/",
    json={"name": "Dumbo", "species": "Elephant", "age": 3}
)
animal = response.json()["data"]
print(f"Created animal ID: {animal['id']}")

# List
response = requests.get(BASE_URL + "/")
animals = response.json()["data"]
print(f"Total animals: {len(animals)}")

# Get
response = requests.get(f"{BASE_URL}/{animal['id']}/")
print(response.json())

# Update
response = requests.put(
    f"{BASE_URL}/{animal['id']}/",
    json={"name": "Dumbo", "species": "Elephant", "age": 4}
)
print(f"Updated: {response.json()}")

# Delete
response = requests.delete(f"{BASE_URL}/{animal['id']}/")
print(f"Deleted: {response.json()}")
```

## 🛠️ Configuration

### Django Settings

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    "apps.animals_app.v1",
]
```

### URL Configuration

```python
# In main urls.py or routing
from apps.animals_app.v1.views import router as animals_router

api.add_router("/animals/", animals_router, tags=["Animals"])
```

## 🎓 Learning Points

This app teaches several important patterns:

### 1. Service Layer Pattern
Separate business logic from views:
```python
# ❌ Bad - Logic in view
@router.post("/")
async def create_animal(request, payload):
    animal = await Animal.objects.acreate(**payload.dict())
    return animal

# ✅ Good - Logic in service
@router.post("/")
async def create_animal(request, payload):
    animal = await AnimalService.create_animal(...)
    return animal
```

### 2. Async/Await Patterns
```python
# Async model operations
animal = await Animal.objects.acreate(...)
animals = [a async for a in Animal.objects.all()]
```

### 3. Proper Error Handling
```python
try:
    result = await operation()
    request.logger.info("Success")
except SpecificError as e:
    request.logger.error(f"Known error: {e}")
except Exception:
    request.logger.exception("Unexpected error")
    raise
```

### 4. Response Consistency
```python
# Consistent response structure
return {
    "data": result,
    "trace_id": str(request.trace_id),
    "error": {}
}
```

## 🚀 Extending the App

### Adding new Fields

```python
# models.py
class Animal(models.Model):
    # ... existing fields
    habitat = models.CharField(max_length=100)
    endangered = models.BooleanField(default=False)

# schemas.py
class AnimalSchema(Schema):
    # ... existing fields
    habitat: str
    endangered: bool
```

### Adding Relationships

```python
class Zoo(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)

class Animal(models.Model):
    # ... existing fields
    zoo = models.ForeignKey(Zoo, on_delete=models.CASCADE)
```

## 📖 Related Documentation

- [Main Project README](../../README.md)
- [Ping App README](../ping_app/README.md)
- [Users App README](../users_app/README.md)
- [Package Manager Guide](../../PACKAGE_MANAGER.md)

---

**Note**: This animals app serves as both a functional CRUD API and a learning resource for Django Ninja patterns. It demonstrates best practices in async operations, logging, service architecture, and API design.
