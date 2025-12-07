# 🔍 Audit App

A powerful, robust, and framework-agnostic audit logging application for Django. It automatically tracks model changes (Create, Update, Delete) and transparently handles both synchronous and asynchronous contexts, supporting background processing via **Celery** or **Dramatiq** with a seamless fallback to inline execution.

## ✨ Key Features

*   **Automated Tracking**: Zero-boilerplate logging. Just add `AUDIT_ENABLED = True` to your models.
*   **Async & Sync Support**: Fully supports Django's Async ORM (`asave`, `adelete`) alongside traditional synchronous methods.
*   **Background Task Integration**: Out-of-the-box support for offloading logs to **Celery** or **Dramatiq** workers to maintain performance.
*   **Smart Fallback**: Automatically runs inline if no background task runner is configured or detected.
*   **Context Awareness**: Captures rich context (Actor ID, Email, IP Address, Trace ID) via middleware using `contextvars`, working seamlessly across views and tasks.
*   **Detailed Diffs**: Stores strict JSON diffs of changes (`old` vs `new` values).
*   **Loose Coupling**: References users via string IDs/Emails, avoiding strict foreign key dependencies on the `Auth` model.

---

## 🚀 Installation & Configuration

### 1. Add to Installed Apps

Ensure the app is registered in your `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = [
    # ...
    "apps.audit_app.v1",
    # ...
]
```

### 2. Configure Middleware

Add `AuditContextMiddleware` to your `MIDDLEWARE` to capture request-scoped context (User, IP, etc.):

```python
MIDDLEWARE = [
    # ...
    "apps.audit_app.v1.middleware.AuditContextMiddleware",
    # ...
]
```

### 3. Async Backend Setup (Optional)

By default, the `audit_app` runs **inline** (synchronously) to ensure reliability. To enable non-blocking background logging, configure one of the supported task runners in `settings.py`:

**For Celery:**
```python
AUDIT_USE_CELERY = True
# AUDIT_USE_DRAMATIQ should be False or omitted
```

**For Dramatiq:**
```python
AUDIT_USE_DRAMATIQ = True
# AUDIT_USE_CELERY should be False or omitted
```

**Fallback Behavior:**
If both are `False` (default), logs are written immediately to the database within the request cycle.

---

## 🛠 Usage

### Automatic Auditing

To enable auditing for a model, simply add the `AUDIT_ENABLED` flag:

```python
from django.db import models

class Animal(models.Model):
    AUDIT_ENABLED = True  # <--- That's it!

    name = models.CharField(max_length=100)
    species = models.CharField(max_length=100)
```

The app automatically monkey-patches and intercepts the following methods:

| Operation | Sync Methods | Async Methods | Action Logged |
| :--- | :--- | :--- | :--- |
| **Create** | `save()`, `objects.create()` | `asave()`* | `CREATE` |
| **Update** | `save()`, `qs.update()` | `asave()`, `qs.aupdate()` | `UPDATE` |
| **Delete** | `delete()`, `qs.delete()` | `adelete()`, `qs.adelete()` | `DELETE` |

*\*Note: `objects.acreate()` internally calls `asave()`, so it is automatically covered without extra patching.*

### Manual Logging

For custom business events (e.g., "Login", "Report Exported", "Permission Changed"), use the `AuditService` directly:

```python
from apps.audit_app.v1.services import AuditService
from common.enums import AuditAction

# Sync
AuditService.log_create_sync(
    action=AuditAction.LOGIN,
    target_model="users.User",
    target_object_id=str(user.id),
    actor_email=user.email,
    changes={"status": "logged_in"}
)

# Async
await AuditService.log_create(
    action=AuditAction.EXPORT,
    target_model="reports.Report",
    target_object_id="N/A",
    changes={"format": "PDF"}
)
```

---

## 🧩 Architecture & Internals

1.  **Bootstrapping**: `AuditAppConfig.ready()` scans all models on startup.
2.  **Patching**: Models with `AUDIT_ENABLED = True` have their data-modifying methods (`save`, `delete`, etc.) wrapped by `AuditPatcher`.
3.  **Context Capture**: Middleware sets context variables (User, IP) at the start of the request.
4.  **Diff Computation**: The patched methods calculate the delta (diff) between the old and new state.
5.  **Dispatching**:
    *   `TaskDispatcher` checks settings (`AUDIT_USE_CELERY` / `AUDIT_USE_DRAMATIQ`).
    *   If enabled, the log payload is sent to the respective task queue (e.g., `audit_log_create_celery_task`).
    *   If disabled, `AuditService` writes the log entry to the DB immediately.

### Data Model (`AuditLog`)

Located in `apps/audit_app/v1/models.py`.

*   **`action`**: CREATE, UPDATE, DELETE, etc.
*   **`target_model`**: String identifier of the model (e.g., `apps.animals.Animal`).
*   **`changes`**: JSONField storing `{'field': {'old': 'A', 'new': 'B'}}`.
*   **`actor_id` / `actor_email`**: Who performed the action.
*   **`trace_id` / `correlation_id`**: For distributed tracing.
