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
    echo "USE_SUPERVISOR is enabled, starting supervisord with gunicorn_supervisord.conf..."
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/gunicorn_supervisord.conf
fi
