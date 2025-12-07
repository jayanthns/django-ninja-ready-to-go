# Audit App

The `audit_app` is a reusable, loosely coupled Django application designed to track system events such as creations, updates, and deletions of objects. It provides a generic `AuditLog` model and a service layer for easy integration with other applications.

## Key Features

- **Loose Coupling**: Does not depend on the `auth.User` model via ForeignKeys. Instead, it stores `actor_id` and `actor_email` as strings, allowing it to be used in microservices or contexts where the user model might vary or be absent.
- **Flexible Actions**: The `action` field is a simple string, allowing you to define and use new action types without requiring database migrations.
- **Generic Tracking**: Can track changes for any model using `target_model` (app_label.model_name) and `target_object_id`.
- **JSON Changes**: Stores detailed changes (before/after states) in a JSONField.

## Architecture

### Model: `AuditLog`

Located in `apps/audit_app/v1/models.py`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `actor_id` | `CharField` | ID of the user/system performing the action. |
| `actor_email` | `CharField` | Email of the user (optional). |
| `action` | `CharField` | Type of action (e.g., "CREATE", "UPDATE", "DELETE"). |
| `target_model` | `CharField` | Path to the model being affected (e.g., "apps.animals_app.Animal"). |
| `target_object_id` | `CharField` | Primary key of the affected object. |
| `changes` | `JSONField` | Dictionary containing details of the change. |
| `ip_address` | `GenericIPAddressField` | IP address of the request. |
| `user_agent` | `TextField` | User agent string of the client. |
| `timestamp` | `DateTimeField` | Auto-generated timestamp of the event. |

### Service: `AuditService`

Located in `apps/audit_app/v1/services.py`.

This service provides static methods to log events. It is designed to be injected or called directly from other services.

#### Methods

- `log_event(...)`: The core method to create an `AuditLog` entry.
- `log_create(instance, ...)`: Helper for logging object creation.
- `log_update(instance, changes, ...)`: Helper for logging object updates.
- `log_delete(instance, ...)`: Helper for logging object deletion.

## Usage

### 1. Defining Actions

Actions are defined in `common/enums.py` to maintain a single source of truth.

```python
# common/enums.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class AuditAction(models.TextChoices):
    CREATE = "CREATE", _("Create")
    UPDATE = "UPDATE", _("Update")
    DELETE = "DELETE", _("Delete")
    LOGIN = "LOGIN", _("Login")
    # Add your custom actions here
    EXPORT = "EXPORT", _("Export Data")
```

**Note**: Since `AuditLog.action` is a simple `CharField`, adding a new value here **does not** require a migration.

### 2. Logging Events

Inject or import `AuditService` in your business logic.

```python
from apps.audit_app.v1.services import AuditService
from common.enums import AuditAction

async def create_animal(self, name: str, user: User):
    # ... create logic ...
    animal = await Animal.objects.acreate(name=name)

    # Log the creation
    await AuditService.log_create(
        instance=animal,
        actor_id=str(user.id),
        actor_email=user.email,
        changes={"name": name},
        ip_address="127.0.0.1" # Optional
    )
```

### 3. Logging Custom Events

For events that don't fit the standard CRUD pattern (e.g., "User logged in", "Report generated"):

```python
await AuditService.log_event(
    action=AuditAction.LOGIN,
    target_model="auth.User",
    target_object_id=str(user.id),
    actor_id=str(user.id),
    actor_email=user.email,
    ip_address=request.META.get("REMOTE_ADDR")
)
```

## Testing

The `audit_app` is designed to be tested without requiring a real database for the audit logs, using `unittest.mock`.

### Example Test

```python
from unittest.mock import patch, AsyncMock
from apps.audit_app.v1.services import AuditService
from common.enums import AuditAction

@pytest.mark.asyncio
async def test_my_service_logs_audit():
    # Mock the DB creation call
    with patch("apps.audit_app.v1.services.AuditLog.objects.acreate", new_callable=AsyncMock) as mock_create:
        
        # Call your service method that triggers the log
        await my_service.do_something()

        # Verify AuditLog was created with expected data
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["action"] == AuditAction.UPDATE
        assert call_kwargs["actor_id"] == "123"
This approach ensures your tests are fast and don't pollute the test database with audit logs.

## Automated Auditing via Patching

Instead of manually calling `AuditService` in every view or service, the application uses an **automated patching mechanism** to intercept and log database changes for models that have `AUDIT_ENABLED = True`.

### How it Works

1. **Initialization**:
   When the Django application starts, the `AuditAppConfig.ready()` method in `apps/audit_app/v1/apps.py` is called. This triggers the `_patch_async_methods()` function.

2. **Model Discovery**:
   The patcher iterates through all registered models in the project using `apps.get_models()`. It checks for an `AUDIT_ENABLED = True` attribute on each model class.

3. **Method Interception**:
   For every enabled model, the following asynchronous methods are monkey-patched (replaced) with wrappers from `apps/audit_app/v1/patch.py`:
   - `model.asave()`: Captures INSERTs and UPDATEs.
   - `model.adelete()`: Captures DELETEs.
   - `model.objects.acreate()`: Captures Manager-level creations.
   - `queryset.aupdate()`: Captures bulk updates.
   - `queryset.adelete()`: Captures bulk deletes.

4. **Context Capture**:
   The `AuditContextMiddleware` (in `apps/audit_app/v1/middleware.py`) captures request-scoped information (User ID, Email, IP, Trace ID) and stores it in a `contextvars.ContextVar`. The patched methods retrieve this context to populate the `actor_id`, `actor_email`, etc., without needing to pass `request` objects through generic model methods.

5. **Change Detection**:
   - **Updates (`asave`)**: The wrapper fetches the "before" state of the object using `aget()`. It then runs the original save, compares the "before" and "after" states, and logs a diff of changed fields.
   - **Creates (`asave`, `acreate`)**: The wrapper logs the new object's state.
   - **Deletes**: The wrapper logs the object's representation before deletion.

### Enabling Auditing for a Model

To enable automated auditing for a model, simply add the `AUDIT_ENABLED` flag:

```python
class MyModel(models.Model):
    AUDIT_ENABLED = True  # <--- Enables automated audit logging
    
    name = models.CharField(max_length=100)
    # ...
```

This drastically reduces boilerplate code and ensures consistent audit trails across the entire application.
