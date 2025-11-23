# Pull base image
FROM python:3.12-slim-bullseye

RUN apt-get update \
    && apt-get install -y netcat supervisor build-essential python3-dev \
    && useradd -m -s /bin/bash appuser # Add appuser

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

# Set work directory
WORKDIR $APP_HOME

# Install dependencies
COPY requirements/requirements.txt requirements/requirements.txt
RUN python -m pip install --upgrade uv pip wheel
RUN python -m uv pip install -r requirements/requirements.txt

# Copy project
COPY . .

# Ensure appuser has ownership of the application directory
RUN chown -R appuser:appuser $APP_HOME

# Copy supervisord configuration
COPY deploy/supervisor_scripts/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY deploy/supervisor_scripts/celery_supervisord.conf /etc/supervisor/conf.d/celery_supervisord.conf
COPY deploy/supervisor_scripts/gunicorn_supervisord.conf /etc/supervisor/conf.d/gunicorn_supervisord.conf

# Change permissions for deploy folder scripts
RUN sed -i 's/\r$//g' /app/deploy/shell_scripts/*.sh /app/deploy/entrypoint_scripts/*.sh
RUN chmod +x /app/deploy/shell_scripts/*.sh /app/deploy/entrypoint_scripts/*.sh

# Ensure that supervisord runs as appuser and log directories are owned by appuser
RUN mkdir -p /var/log/supervisor \
    && chown -R appuser:appuser /var/log/supervisor

# Switch to appuser to run the container
USER appuser

# Run the entrypoint script as the appuser
EXPOSE 8000

CMD ["/app/deploy/entrypoint_scripts/entrypoint.sh"]
