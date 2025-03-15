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

# Change to `src/` directory
cd src || { echo "Failed to change directory to src"; exit 1; }

# Configuration Variables
WORKER_COUNT=${CELERY_WORKERS:-4}  # Number of Celery workers
CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-4}  # Number of concurrent processes per worker
PREFETCH_MULTIPLIER=${CELERY_PREFETCH_MULTIPLIER:-8}
POOL=${CELERY_POOL:-gevent}
CELERY_QUEUE_NAME=${CELERY_QUEUE_NAME:-django_ninja_queue}  # Default queue

# Logging
echo "Starting ${WORKER_COUNT} Celery workers on queue '${CELERY_QUEUE_NAME}' with concurrency=${CONCURRENCY}, pool=${POOL}, prefetch-multiplier=${PREFETCH_MULTIPLIER}"

# Trap SIGTERM and SIGINT to stop workers gracefully
trap 'kill $(jobs -p); wait' SIGTERM SIGINT

# Start Celery workers with unique names, binding them to the specified queue
for i in $(seq 1 $WORKER_COUNT); do
    echo "Launching Celery worker $i for queue '${CELERY_QUEUE_NAME}'..."
    celery -A main worker --loglevel=info --concurrency=${CONCURRENCY} \
        --pool=${POOL} --prefetch-multiplier=${PREFETCH_MULTIPLIER} \
        --without-gossip --without-mingle --without-heartbeat \
        -n worker$i@%h -Q ${CELERY_QUEUE_NAME} &  # Assign worker to specific queue
done

# Keep the container running
wait
