# 🧪 Testing Guide

This project uses `pytest` for testing. This guide covers how to run tests and resolve common issues.

## 🚀 Running Tests

To run the full test suite with coverage report:

```bash
make pytest
```

This command will:

1. Run all tests using `pytest`
2. Generate a coverage report
3. Save the HTML report to `coverage_html_report/`

## 🔧 Troubleshooting

### PostgreSQL Collation Mismatch

**Error:**

```bash
django.db.utils.InternalError: template database "template1" has a collation version mismatch
DETAIL: The template database was created using collation version 2.36, but the operating system provides version 2.41.
```

**Cause:**
This occurs when the PostgreSQL container's operating system libraries (glibc/ICU) are updated, but the database data volume was initialized with an older version.

**Fix:**
Run the following commands to update the collation version for the system databases inside the running container:

```bash
# 1. Fix the template1 database
docker exec django_ninja_db_container psql -U postgres -c "ALTER DATABASE template1 REFRESH COLLATION VERSION;"

# 2. Fix the main postgres database
docker exec django_ninja_db_container psql -U postgres -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;"
```

After running these commands, try running `make pytest` again.
