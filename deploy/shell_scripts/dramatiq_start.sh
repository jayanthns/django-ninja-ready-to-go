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


# Configuration Variables (Defaults if not set)
CONCURRENCY=${DRAMATIQ_WORKER_CONCURRENCY:-2}
POOL=${DRAMATIQ_POOL:-gevent}
QUEUE_NAME=${DRAMATIQ_QUEUE_NAME:-django_ninja_dramatiq_queue}

# Logging
echo "Starting Dramatiq worker on queue '${QUEUE_NAME}' with concurrency=${CONCURRENCY}, pool=${POOL}"

# Determine command based on pool
if [ "$POOL" = "gevent" ]; then
    # For gevent, we use dramatiq-gevent
    # We set --processes 1 because Supervisor manages the number of worker processes
    # We set --threads to CONCURRENCY (greenlets per process)
    CMD="dramatiq-gevent"
    ARGS="--processes 1 --threads ${CONCURRENCY}"
else
    # Standard dramatiq
    CMD="dramatiq"
    ARGS="--processes 1 --threads ${CONCURRENCY}"
fi

# Start a single Dramatiq worker bound to the specified queue
exec $CMD main.dramatiq $ARGS -Q ${QUEUE_NAME}
