# 🧪 Testing Guide

This project uses two complementary testing approaches:

1. **Pytest**: For unit tests, service-level integration tests, and standard Django tests.
2. **Custom API Test Suite**: For end-to-end API flow verification against a live server.

---

## 🚀 1. Standard Tests (Pytest)

Used for testing individual components, services, and models.

### Running Pytest

To run the full test suite with coverage report:

```bash
make pytest
```

This command will:

1. Run all tests using `pytest`
2. Generate a coverage report
3. Save the HTML report to `coverage_html_report/`

---

## ⚡ 2. Custom API Test Suite (End-to-End)

The **Custom API Test Suite** is designed to verify complete application flows (e.g., "Register -> Login -> Create Item -> List Items") against a **real, running server** instance connected to a **dedicated test database**.

### Key Features

- **Live Server**: Starts a temporary Uvicorn instance on port `8001`.
- **Isolated DB**: Automatically creates and drops `test_db_api`.
- **Strict Contract**: Enforces exact JSON structure matching.
- **Scenario-Based**: Tests are written as sequential user stories.

### Running API Tests

To run the API test suite:

```bash
make test-api
```

### Directory Structure (`api_tests/`)

- **`runner.py`**: Main orchestrator. Sets up DB, starts server, runs scenarios.
- **`client.py`**: A wrapper around `requests` to handle base URL and auth tokens.
- **`assertions.py`**: Helpers for strict structure validation.
- **`utils.py`**: Database and server management utilities.
- **`scenarios/`**: Folder containing individual test scripts (e.g., `auth.py`, `animals.py`).

### Writing a New Scenario

1. **Create a file** in `api_tests/scenarios/` (e.g., `my_flow.py`).
2. **Define a `run` function** that accepts `client`.
3. **Implement the flow**:

```python
from api_tests.client import APIClient
from api_tests.assertions import assert_structure

def run(client: APIClient):
    print("Running My Flow...")
    
    # Define expected structure (Strict Contract)
    expected_response = {
        "data": {
            "id": str,
            "name": str
        },
        "trace_id": str,
        "error": (dict, type(None))
    }

    # 1. Perform Action
    payload = {"name": "Test Item"}
    resp = client.post("/api/v1/items/", json=payload)
    assert resp.status_code == 200, f"Failed: {resp.text}"
    
    # 2. Validate Structure & Data
    data = resp.json()
    assert_structure(data, expected_response, path="create_item")
    assert data["data"]["name"] == "Test Item"
    
    print("My Flow Passed.")
```

4. **Register the scenario** in `api_tests/runner.py`:

```python
from api_tests.scenarios import my_flow
# ...
my_flow.run(client)
```

---

## 📜 API Contract Testing

To ensure "100% safe" API modifications, the API test suite enforces **strict structure validation**.

**The Rule**:
> Any change to the API response structure (adding/removing fields, changing types) MUST cause a test failure.

**How to Handle API Changes**:

1. **Modify Code**: Update your Schema/View.
2. **Run Tests**: `make test-api` will fail (e.g., "Unexpected key 'new_field'").
3. **Update Contract**: Consciously update the `expected_structure` in the test scenario.
4. **Verify**: Run `make test-api` again.

---

## 🔧 Troubleshooting

### PostgreSQL Collation Mismatch

**Error:**

```bash
django.db.utils.InternalError: template database "template1" has a collation version mismatch
```

**Fix:**

```bash
# 1. Fix the template1 database
docker exec django_ninja_db_container psql -U postgres -c "ALTER DATABASE template1 REFRESH COLLATION VERSION;"

# 2. Fix the main postgres database
docker exec django_ninja_db_container psql -U postgres -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;"
```
