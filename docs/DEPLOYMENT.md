# 🚀 Deployment Guide

This guide covers the deployment configuration, scenarios, and file references for the Django Ninja project.

## 📂 Deployment Directory Structure

The `deploy/` directory contains all necessary scripts for production deployment. The behavior is controlled by environment variables in `.env`.

### Configuration Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_SUPERVISOR` | `true` | **Enabled**: Uses Supervisor (recommended). **Disabled**: Runs Gunicorn directly (for orchestration). |
| `RUN_CELERY_TOGETHER` | `false` | **Enabled**: Runs Gunicorn and Celery together (requires Supervisor). **Disabled**: Runs only Gunicorn. |

## 🌍 Deployment Scenarios

### 1. Standard Production (Recommended)
-   `USE_SUPERVISOR=true`
-   `RUN_CELERY_TOGETHER=false`
-   **Result**: The container runs Gunicorn managed by Supervisor. Celery workers should be run in separate containers using the same image but overriding the command (e.g., `celery -A main worker`).

### 2. All-in-One (Low Resource)
-   `USE_SUPERVISOR=true`
-   `RUN_CELERY_TOGETHER=true`
-   **Result**: The container runs both Gunicorn and Celery managed by a single Supervisor instance.
-   *Note: You must uncomment the Celery section in `deploy/supervisor_scripts/supervisord.conf` to enable this.*

### 3. Simple / Orchestrated
-   `USE_SUPERVISOR=false`
-   **Result**: The container runs Gunicorn directly as the entrypoint process. Useful if you are using Kubernetes or another orchestrator to manage process lifecycles directly.

## 📄 Deployment Files Reference

Here is a guide to the files in the `deploy/` directory and when to use them:

### 1. Entrypoint Scripts (`deploy/entrypoint_scripts/`)
These are the main entry points for the Docker container.

-   **`entrypoint.sh`**: **[Primary]** The default command for the Docker image. It loads environment variables, checks the `USE_SUPERVISOR` flag, and decides whether to start Supervisor or run Gunicorn directly.
-   **`gunicorn_entrypoint.sh`**: A specific entrypoint that forces the use of Supervisor with the Gunicorn configuration. Use this if you want to bypass the logic in `entrypoint.sh` and strictly run Gunicorn via Supervisor.

### 2. Supervisor Configurations (`deploy/supervisor_scripts/`)
Configuration files for Supervisor, which manages processes inside the container.

-   **`supervisord.conf`**: **[Primary]** The main configuration file used when `RUN_CELERY_TOGETHER=true`. It can manage multiple processes (Gunicorn + Celery).
-   **`gunicorn_supervisord.conf`**: Used when `RUN_CELERY_TOGETHER=false`. It configures Supervisor to manage *only* Gunicorn.
-   **`celery_supervisord.conf`**: A standalone configuration for running Celery workers under Supervisor. Use this if you are building a dedicated Celery worker container that uses Supervisor.

### 3. Shell Scripts (`deploy/shell_scripts/`)
Actual startup scripts called by Supervisor or the entrypoints.

-   **`gunicorn_start.sh`**: Prepares the environment (migrations, static files) and starts the Gunicorn server.
-   **`celery_start.sh`**: Starts a single Celery worker instance.
-   **`celery_multiple_workers_start.sh`**: Starts multiple Celery workers based on the `CELERY_WORKERS` environment variable.

### 4. Database Scripts (`deploy/db_scripts/`)
-   **`init_schema.sh`**: Helper script to initialize the database schema, often used in CI/CD pipelines or initial setup.
