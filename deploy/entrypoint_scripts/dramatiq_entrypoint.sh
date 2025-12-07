#!/bin/sh

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

# Start supervisord with the dramatiq_supervisord.conf
echo "Starting supervisord with dramatiq_supervisord.conf..."
/usr/bin/supervisord -c /etc/supervisor/conf.d/dramatiq_supervisord.conf

# Keep the container running
exec "$@"
