#!/bin/sh

# Load environment variables from env/.env file
echo "Loading the environment variables..."
if [ -f env/.env ]; then
    set -a
    . env/.env || handle_error "Failed to load environment variables"
    set +a
    echo "Environment variables loaded successfully."
else
    echo "Warning: env/.env file not found. Skipping environment variable loading."
fi

# Default USE_SUPERVISOR to true if not set
if [ -z "${USE_SUPERVISOR}" ]; then
    echo "WARNING: Environment variable [USE_SUPERVISOR] not found, setting to default (true)" >&2
    USE_SUPERVISOR=true
fi

# Normalize to lowercase
USE_SUPERVISOR=$(echo "$USE_SUPERVISOR" | tr '[:upper:]' '[:lower:]')

if [ "$USE_SUPERVISOR" = "false" ]; then
    echo "Skipping Supervisor: Running Uvicorn directly via gunicorn_start.sh"
    exec /app/deploy/shell_scripts/gunicorn_start.sh
else
    echo "USE_SUPERVISOR is enabled, proceeding with Supervisor setup..."

    # Check if the environment variable RUN_CELERY_TOGETHER is set, defaulting to false
    if [ -z "${RUN_CELERY_TOGETHER}" ]; then
        echo "WARNING: Environment variable [RUN_CELERY_TOGETHER] not found, setting to default (false)" >&2
        RUN_CELERY_TOGETHER=false
    fi

    # Normalize to lowercase
    RUN_CELERY_TOGETHER=$(echo "$RUN_CELERY_TOGETHER" | tr '[:upper:]' '[:lower:]')

    # Start the appropriate Supervisor configuration
    if [ "$RUN_CELERY_TOGETHER" = "true" ]; then
        echo "Starting supervisord with both Uvicorn and Celery..."
        exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
    else
        echo "Starting supervisord with Uvicorn only..."
        exec /usr/bin/supervisord -c /etc/supervisor/conf.d/gunicorn_supervisord.conf
    fi
fi
