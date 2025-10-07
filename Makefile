# Detect the operating system
ifeq ($(OS),Windows_NT)
	# Windows
	VENV_ACTIVATE = .\venv\Scripts\activate
else
	# Unix-based systems (Linux/Mac)
	VENV_ACTIVATE = source ./venv/bin/activate
endif

kill-port:
	@echo "Killing processes using port 8000..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No processes found on port 8000"

run: kill-port
	@echo "Running Django development server..."
	@$(VENV_ACTIVATE) && cd src && python manage.py runserver

makemigrations:
	@echo "Creating Django database migrations..."
	@$(VENV_ACTIVATE) && cd src && python manage.py makemigrations

migrate:
	@echo "Applying Django database migrations..."
	@$(VENV_ACTIVATE) && cd src && python manage.py migrate

shell:
	@echo "Logging into the Django shell..."
	@$(VENV_ACTIVATE) && python manage.py shell

shell_plus:
	@echo "Logging into the Django Shell Plus"
	@$(VENV_ACTIVATE) && python manage.py shell_plus

createsuperuser:
	@echo "Create superuser..."

run_uvicorn:
	@echo "Running uvicorn..."
	@$(VENV_ACTIVATE) && cd src && uvicorn main.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --reload


# Initialize the venv and install the requirements

init:
	python3 -m pip install uv
	uv venv venv
	@$(MAKE) install


install:
	@$(VENV_ACTIVATE) && uv pip install --upgrade pip-tools pip wheel
	@$(VENV_ACTIVATE) && uv pip install --upgrade -r requirements/requirements.txt -r requirements/local_requirements.txt


update-deps:
	@$(VENV_ACTIVATE) && uv pip compile --upgrade --resolver backtracking -o requirements/requirements.txt requirements_raw/requirements.in
	@$(VENV_ACTIVATE) && uv pip compile --upgrade --resolver backtracking -o requirements/local_requirements.txt requirements_raw/local_requirements.in


package-sync: update-deps install
sync-packages: package-sync
sync-package: package-sync


.PHONY: run kill-port makemigrations migrate shell createsuperuser update-deps install update init

isort_check:
	@echo "Running isort check..."
	@$(VENV_ACTIVATE) && isort --check-only .

black_check:
	@echo "Running black check..."
	@$(VENV_ACTIVATE) &&  black --check .

flake8:
	@echo "Running flake8 check..."
	@$(VENV_ACTIVATE) &&  flake8 .

static-tests: isort_check black_check flake8

pytest-run:
	@echo "Running Pytest"
	@echo "pytest --cov --cov-report=html"
	@$(VENV_ACTIVATE) &&  pytest --cov --cov-report=html

dynamic-test: pytest-run
run-tests: pytest-run
pytest: pytest-run

pytest-open-report:
	@echo "Opening Pytest Report"
	@echo "open coverage_html_report/index.html"
	@$(VENV_ACTIVATE) &&  open coverage_html_report/index.html

test-report: pytest-open-report

# Docker related

run_docker_compose:
	docker compose -f docker-compose.yaml up --build

start_docker_compose: run_docker_compose

stop_docker_compose:
	docker compose -f docker-compose.yaml down

d_shell:
	docker exec -it django_ninja_api_container /bin/bash

d-db:
	docker compose -f docker-compose.yaml up -d django_ninja_db

d-redis:
	docker compose -f docker-compose.yaml up -d django_ninja_redis_svc

d-db-logs:
	docker compose -f docker-compose.yaml logs django_ninja_db

d-redis-logs:
	docker compose -f docker-compose.yaml logs django_ninja_redis_svc

d-db-and-redis:
	docker compose -f docker-compose.yaml up -d django_ninja_db django_ninja_redis_svc

d-db-and-redis-down:
	docker compose -f docker-compose.yaml down django_ninja_db django_ninja_redis_svc

d-db-and-redis-restart:
	docker compose -f docker-compose.yaml restart django_ninja_db django_ninja_redis_svc

d-up:
	docker compose -f docker-compose.yaml up -d

d-down:
	docker compose -f docker-compose.yaml down

d-restart:
	docker compose -f docker-compose.yaml restart

d-logs:
	docker compose -f docker-compose.yaml logs

d-ps:
	docker compose -f docker-compose.yaml ps

d-build:
	docker compose -f docker-compose.yaml build

d-pull:
	docker compose -f docker-compose.yaml pull

d-push:
	docker compose -f docker-compose.yaml push

d-exec:
	docker exec -it django_ninja_api_container /bin/bash

help:
	@echo "Available Makefile commands:"
	@echo "  run: Run the Django development server (automatically kills port 8000 first)"
	@echo "  kill-port: Kill processes using port 8000"
	@echo "  makemigrations: Create Django database migrations"
	@echo "  migrate: Apply Django database migrations"
	@echo "  shell: Log into the Django shell"
	@echo "  shell_plus: Log into the Django Shell Plus"
	@echo "  createsuperuser: Create a superuser"
	@echo "  run_uvicorn: Run the uvicorn server"
	@echo "  init: Initialize the venv and install the requirements"
	@echo "  install: Install the requirements"
	@echo "  update-deps: Update the dependencies"
	@echo "  package-sync: Update the dependencies and install the requirements"
	@echo "  isort_check: Run isort check"
	@echo "  black_check: Run black check"
	@echo "  flake8: Run flake8 check"
	@echo "  static-tests: Run isort, black, and flake8 checks"
	@echo "  pytest-run: Run pytest"
	@echo "  dynamic-test: Run pytest"
	@echo "  run-tests: Run pytest"
	@echo "  pytest: Run pytest"
	@echo "  pytest-open-report: Open the pytest report"
	@echo "  test-report: Open the pytest report"
	@echo "  d-shell: Log into the Django shell"
	@echo "  d-db: Start the Django database"
	@echo "  d-redis: Start the Redis service"
	@echo "  d-db-logs: Show the Django database logs"
	@echo "  d-redis-logs: Show the Redis logs"
	@echo "  d-db-and-redis: Start the Django database and Redis service"
	@echo "  d-db-and-redis-down: Stop the Django database and Redis service"
	@echo "  d-db-and-redis-restart: Restart the Django database and Redis service"
	@echo "  d-up: Start the services"
	@echo "  d-down: Stop the services"
	@echo "  d-restart: Restart the services"
	@echo "  d-logs: Show the logs"
	@echo "  d-ps: Show the services"
	@echo "  d-build: Build the services"
	@echo "  d-pull: Pull the services"
	@echo "  d-push: Push the services"
	@echo "  d-exec: Execute a command in the services"
	@echo "  help: Show this help message"

.PHONY: run makemigrations migrate shell shell_plus createsuperuser run_uvicorn init install update-deps package-sync isort_check black_check flake8 static-tests pytest-run dynamic-test run-tests pytest pytest-open-report test-report d-shell d-db d-redis d-db-logs d-redis-logs d-db-and-redis d-db-and-redis-down d-db-and-redis-restart d-up d-down d-restart d-logs d-ps d-build d-pull d-push d-exec help
