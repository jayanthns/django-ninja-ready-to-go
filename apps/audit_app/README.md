# Audit App

The `audit_app` is a reusable, loosely coupled Django application designed to track system events such as creations, updates, and deletions of objects. It provides a generic `AuditLog` model and a mechanism for **automated audit logging** via monkey-patching.

## Key Features

- **Loose Coupling**: Does not depend on the `auth.User` model via ForeignKeys. Instead, it stores `actor_id` and `actor_email` as strings, allowing it to be used in microservices or contexts where the user model might vary.
- **Automated Tracking**: Automatically intercepts Sync and Async database operations (`save`, `delete`, `update`, `create`) for models with `AUDIT_ENABLED = True`.
- **Context Awareness**: Captures the "Actor" (User/Service) performing the action using Django's `contextvars`, working seamlessly across views and background tasks.
- **JSON Changes**: Stores detailed changes (before/after states) in a JSONField.
- **Async & Sync Support**: Fully supports Django's async ORM capabilities (`asave`, `acreate`, etc.) alongside traditional sync methods.

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
| `changes` | `JSONField` | Dictionary containing details of the change (diff). |
| `ip_address` | `GenericIPAddressField` | IP address of the request. |
| `timestamp` | `DateTimeField` | Auto-generated timestamp of the event. |

### Core Logic: `AuditPatcher`

Located in `apps/audit_app/v1/patcher.py`.

This class is responsible for computing diffs and dispatching log events. It serves as the central handler for the patched model methods.

## Installation & Configuration

### 1. Add to Installed Apps

Ensure the app is added to your `INSTALLED_APPS` (usually done automatically by the project structure, but good to verify):

```python
INSTALLED_APPS = [
    # ...
    "apps.audit_app.v1",
    # ...
]
```

### 2. Add Middleware

To capture the user context (who is performing the action) from HTTP requests, add the `AuditContextMiddleware` to your `MIDDLEWARE` setting:

```python
MIDDLEWARE = [
    # ...
    "apps.audit_app.v1.middleware.AuditContextMiddleware",
    # ...
]
```

 This middleware uses `contextvars` to store the request user/IP, making it available to the deep model-level patches without passing `request` objects around.

## Usage

### Enabling Automated Auditing

The easiest way to track a model is to simply set `AUDIT_ENABLED = True` on the model class.

```python
class Animal(models.Model):
    AUDIT_ENABLED = True  # <--- Enables automated audit logging

    name = models.CharField(max_length=100)
    # ...
```

Once enabled, the `audit_app` will automatically track:

| Operation | Method(s) Intercepted | Action Logged |
| :--- | :--- | :--- |
| **Create** | `save()`, `asave()`, `objects.create()`, `objects.acreate()` | `CREATE` |
| **Update** | `save()`, `asave()`, `qs.update()`, `qs.aupdate()` | `UPDATE` |
| **Delete** | `delete()`, `adelete()`, `qs.delete()`, `qs.adelete()` | `DELETE` |

### Manual Logging (Custom Events)

For events that fall outside standard CRUD (e.g., "Login", "Export", "Report Generated"), you can use the `AuditService` directly.

```python
from apps.audit_app.v1.services import AuditService
from common.enums import AuditAction

async def generate_report(user):
    # ... logic ...
    
    await AuditService.log_event(
        action=AuditAction.EXPORT,
        target_model="reports.Report",
        target_object_id="N/A",
        actor_id=str(user.id),
        actor_email=user.email,
        changes={"type": "pdf_export"}
    )
```

## How It Works (Internals)

1.  **Bootstrapping**: When Django starts, `AuditAppConfig.ready()` (in `apps.py`) scans all models.
2.  **Patching**: If a model has `AUDIT_ENABLED = True`, its methods (`save`, `delete`, etc.) are monkey-patched with wrappers from `AuditPatcher`.
3.  **Execution**:
    *   When you call `animal.save()`, the wrapper runs using `AuditPatcher.save`.
    *   It checks if it's a new record or an update.
    *   It computes the delta (diff) of changes.
    *   It calls `AuditService` to write the log entry.
    *   Finally, it executes the original `save()` method.
