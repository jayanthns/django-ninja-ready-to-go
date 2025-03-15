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

# Configuration Variables (Defaults if not set)
CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-4}
PREFETCH_MULTIPLIER=${CELERY_PREFETCH_MULTIPLIER:-8}
POOL=${CELERY_POOL:-gevent}
CELERY_QUEUE_NAME=${CELERY_QUEUE_NAME:-django_ninja_queue}  # Default queue

# Logging
echo "Starting Celery worker on queue '${CELERY_QUEUE_NAME}' with concurrency=${CONCURRENCY}, pool=${POOL}, prefetch-multiplier=${PREFETCH_MULTIPLIER}"

# Start a single Celery worker bound to the specified queue
exec celery -A src.main worker --loglevel=info \
    --concurrency=${CONCURRENCY} \
    --pool=${POOL} \
    --prefetch-multiplier=${PREFETCH_MULTIPLIER} \
    --without-gossip --without-mingle --without-heartbeat \
    -Q ${CELERY_QUEUE_NAME}  # Bind to specific queue
