#!/bin/bash

# Load environment variables from env/.env file
echo "Loading the environment variables..."
if [ -f env/.env ]; then
    set -a
    . env/.env || { echo "Failed to load environment variables"; exit 1; }
    set +a
    echo "Environment variables loaded successfully."
else
    echo "Warning: env/.env file not found. Skipping environment variable loading."
fi

# Set default workers to 4 if UVICORN_WORKERS is not set
WORKERS=${UVICORN_WORKERS:-4}


# Start Gunicorn with Uvicorn workers
exec gunicorn main.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers $WORKERS \
  --timeout 130 \
  --graceful-timeout 130 \
  --keep-alive 60 \
  --log-level info \
  --access-logfile - \
  --error-logfile -
