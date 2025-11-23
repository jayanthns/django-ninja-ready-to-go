# 🛠️ Manual Setup Guide

This guide explains how to set up the project manually without using the provided `Makefile`. This is useful if you prefer direct control or are on a system where `make` is not available.

## Prerequisites

-   Python 3.10+
-   `uv` package manager (or pip)
-   PostgreSQL
-   Redis (optional, for caching/Celery)

## Step-by-Step Setup

### 1. Install `uv`
```bash
pip install uv
```

### 2. Create a virtual environment
```bash
uv venv venv
```

### 3. Activate the virtual environment
```bash
source venv/bin/activate
# Windows: venv\Scripts\activate
```

### 4. Install dependencies
**Important**: You must set `UV_PROJECT_ENVIRONMENT` to your venv path so `uv` knows where to install packages.

```bash
export UV_PROJECT_ENVIRONMENT=$(pwd)/venv
uv sync --all-extras
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Start the server
```bash
python manage.py runserver
```

## Next Steps
-   Access the API at `http://localhost:8000/api/docs`
-   Check [Testing Guide](testing.md) to run tests.
