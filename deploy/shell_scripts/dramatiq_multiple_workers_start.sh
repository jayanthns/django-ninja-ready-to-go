#!/bin/bash

# Load environment variables from env/.env file
# echo "Loading the environment variables..."
# if [ -f env/.env ]; then
#     set -a
#     . env/.env || handle_error "Failed to load environment variables"
#     set +a
#     echo "Environment variables loaded successfully."
# else
#     echo "Warning: env/.env file not found. Skipping environment variable loading."
# fi


# Configuration Variables
WORKER_COUNT=${DRAMATIQ_WORKERS:-2}
CONCURRENCY=${DRAMATIQ_WORKER_CONCURRENCY:-2}
POOL=${DRAMATIQ_POOL:-gevent}
QUEUE_NAME=${DRAMATIQ_QUEUE_NAME:-django_ninja_dramatiq_queue}

# Logging
echo "Starting ${WORKER_COUNT} Dramatiq workers on queue '${QUEUE_NAME}' with concurrency=${CONCURRENCY}, pool=${POOL}"

# Determine command based on pool
if [ "$POOL" = "gevent" ]; then
    CMD="dramatiq-gevent"
    ARGS="--processes 1 --threads ${CONCURRENCY}"
else
    CMD="dramatiq"
    ARGS="--processes 1 --threads ${CONCURRENCY}"
fi

# Trap SIGTERM and SIGINT to stop workers gracefully
trap 'kill $(jobs -p); wait' SIGTERM SIGINT

# Start Dramatiq workers
for i in $(seq 1 $WORKER_COUNT); do
    echo "Launching Dramatiq worker $i for queue '${QUEUE_NAME}'..."
    $CMD main.dramatiq $ARGS -Q ${QUEUE_NAME} &
done

# Keep the container running
wait
