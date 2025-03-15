#!/bin/bash

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

# Set default workers to 4 if UVICORN_WORKERS is not set
WORKERS=${UVICORN_WORKERS:-4}

uvicorn src.main.asgi:application \
  --host 0.0.0.0 \
  --port 8000 \
  --workers $WORKERS \
  --timeout-keep-alive 60 \
  --timeout-graceful-shutdown 130 \
  --log-level info \
  --access-log
