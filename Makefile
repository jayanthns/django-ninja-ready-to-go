# Detect the operating system
ifeq ($(OS),Windows_NT)
	# Windows
	VENV_ACTIVATE = .\venv\Scripts\activate
else
	# Unix-based systems (Linux/Mac)
	VENV_ACTIVATE = source ./venv/bin/activate
	# Ensure uv uses the correct virtual environment
	export UV_PROJECT_ENVIRONMENT = $(shell pwd)/venv
endif

kill-port:
	@echo "Killing processes using port 8000..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No processes found on port 8000"

run: kill-port
	@echo "Running Django development server..."
	@$(VENV_ACTIVATE) && python manage.py runserver

makemigrations:
	@echo "Creating Django database migrations..."
	@$(VENV_ACTIVATE) && python manage.py makemigrations

migrate:
	@echo "Applying Django database migrations..."
	@$(VENV_ACTIVATE) && python manage.py migrate

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
	@$(VENV_ACTIVATE) && uvicorn main.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --reload

run_gunicorn:
	@echo "Running gunicorn..."
	@$(VENV_ACTIVATE) && gunicorn main.asgi:application --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker

generate-docs:
	@echo "Generating API documentation..."
	@$(VENV_ACTIVATE) && python manage.py generate_api_docs

open-docs: swagger

swagger: generate-docs
	@echo "Serving Swagger UI at http://localhost:8002/swagger.html"
	@echo "Press Ctrl+C to stop."
	@if [ -n "$$WSL_DISTRO_NAME" ]; then \
		(sleep 1 && wslview http://localhost:8002/swagger.html) & \
	elif [ "$$(uname)" = "Darwin" ]; then \
		(sleep 1 && open http://localhost:8002/swagger.html) & \
	elif [ "$$(expr substr $$(uname -s) 1 5)" = "Linux" ]; then \
		(sleep 1 && xdg-open http://localhost:8002/swagger.html) & \
	elif [ "$$(expr substr $$(uname -s) 1 10)" = "MINGW32_NT" ] || [ "$$(expr substr $$(uname -s) 1 10)" = "MINGW64_NT" ]; then \
		(sleep 1 && start http://localhost:8002/swagger.html) & \
	fi
	@$(VENV_ACTIVATE) && python -m http.server 8002 --directory docs

redoc: generate-docs
	@echo "Serving ReDoc at http://localhost:8002/redoc.html"
	@echo "Press Ctrl+C to stop."
	@if [ -n "$$WSL_DISTRO_NAME" ]; then \
		(sleep 1 && wslview http://localhost:8002/redoc.html) & \
	elif [ "$$(uname)" = "Darwin" ]; then \
		(sleep 1 && open http://localhost:8002/redoc.html) & \
	elif [ "$$(expr substr $$(uname -s) 1 5)" = "Linux" ]; then \
		(sleep 1 && xdg-open http://localhost:8002/redoc.html) & \
	elif [ "$$(expr substr $$(uname -s) 1 10)" = "MINGW32_NT" ] || [ "$$(expr substr $$(uname -s) 1 10)" = "MINGW64_NT" ]; then \
		(sleep 1 && start http://localhost:8002/redoc.html) & \
	fi
	@$(VENV_ACTIVATE) && python -m http.server 8002 --directory docs

create-app:
	@if [ -z "$(APP)" ]; then \
		echo "Error: APP name is required"; \
		echo "Usage: make create-app APP=your_app_name"; \
		exit 1; \
	fi
	@bash scripts/create_ninja_app.sh $(APP)


# Initialize the venv and install the requirements

init:
	python3 -m pip install uv
	uv venv venv
	@$(MAKE) install


install:
	@echo "Installing dependencies with uv..."
	@uv sync --all-extras


# Legacy install command (for backward compatibility with old requirements.txt workflow)
install-legacy:
	@$(VENV_ACTIVATE) && uv pip install --upgrade pip-tools pip wheel
	@$(VENV_ACTIVATE) && uv pip install --upgrade -r requirements/requirements.txt -r requirements/local_requirements.txt


update-deps:
	@echo "Upgrading all dependencies..."
	@uv lock --upgrade
	@uv sync --all-extras


# Compile dependencies without upgrading (lock current versions in pyproject.toml)
compile-deps:
	@echo "Locking dependencies from pyproject.toml..."
	@uv lock
	@uv sync --all-extras


# Add a package to production dependencies
add-package:
	@echo "Usage: make add-package PACKAGE=<package-name> [VERSION=<version>]"
	@if [ -z "$(PACKAGE)" ]; then \
		echo "Error: PACKAGE is required. Example: make add-package PACKAGE=requests VERSION=2.31.0"; \
		exit 1; \
	fi
	@if [ -z "$(VERSION)" ]; then \
		uv add $(PACKAGE); \
		echo "Added '$(PACKAGE)' to dependencies"; \
	else \
		uv add "$(PACKAGE)==$(VERSION)"; \
		echo "Added '$(PACKAGE)==$(VERSION)' to dependencies"; \
	fi


# Add a package to dev dependencies
add-dev-package:
	@echo "Usage: make add-dev-package PACKAGE=<package-name> [VERSION=<version>]"
	@if [ -z "$(PACKAGE)" ]; then \
		echo "Error: PACKAGE is required. Example: make add-dev-package PACKAGE=pytest VERSION=8.3.3"; \
		exit 1; \
	fi
	@if [ -z "$(VERSION)" ]; then \
		uv add --optional dev $(PACKAGE); \
		echo "Added '$(PACKAGE)' to dev dependencies"; \
	else \
		uv add --optional dev "$(PACKAGE)==$(VERSION)"; \
		echo "Added '$(PACKAGE)==$(VERSION)' to dev dependencies"; \
	fi


# Remove a package from production dependencies
remove-package:
	@echo "Usage: make remove-package PACKAGE=<package-name>"
	@if [ -z "$(PACKAGE)" ]; then \
		echo "Error: PACKAGE is required. Example: make remove-package PACKAGE=requests"; \
		exit 1; \
	fi
	@uv remove $(PACKAGE)
	@echo "Removed '$(PACKAGE)' from dependencies"


# Remove a package from dev dependencies
remove-dev-package:
	@echo "Usage: make remove-dev-package PACKAGE=<package-name>"
	@if [ -z "$(PACKAGE)" ]; then \
		echo "Error: PACKAGE is required. Example: make remove-dev-package PACKAGE=pytest"; \
		exit 1; \
	fi
	@uv remove --optional dev $(PACKAGE)
	@echo "Removed '$(PACKAGE)' from dev dependencies"


# Export to legacy requirements.txt format (for deployment/CI compatibility)
export-requirements:
	@echo "Exporting uv.lock to requirements.txt format..."
	@uv export --format requirements-txt --no-hashes > requirements.txt
	@uv export --format requirements-txt --no-hashes --extra dev > requirements-dev.txt
	@echo "Exported to requirements.txt and requirements-dev.txt"


package-sync: update-deps
sync-packages: package-sync
sync-package: package-sync


.PHONY: run kill-port makemigrations migrate shell shell_plus createsuperuser run_uvicorn run_gunicorn generate-docs create-app init install compile-deps add-package add-dev-package remove-package remove-dev-package update-deps pytest black_check black_format isort_check isort_format flake8 mypy static-tests d-build d-up d-down d-logs d-restart d-exec help

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
	@echo "Running Pytest with Coverage"
	@echo "pytest --cov --cov-report=html"
	@$(VENV_ACTIVATE) &&  pytest --cov --cov-report=html

test-api:
	@echo "Running API tests..."
	@$(VENV_ACTIVATE) && python -m api_tests.runner

pytest-v:
	@echo "Running Pytest (Verbose)"
	@$(VENV_ACTIVATE) && pytest -v

pytest-q:
	@echo "Running Pytest (Quiet)"
	@$(VENV_ACTIVATE) && pytest -q

pytest-lf:
	@echo "Running Pytest (Last Failed)"
	@$(VENV_ACTIVATE) && pytest --lf

pytest-x:
	@echo "Running Pytest (Exit on First Failure)"
	@$(VENV_ACTIVATE) && pytest -x

pytest-slow:
	@echo "Running Pytest (Show Slowest Tests)"
	@$(VENV_ACTIVATE) && pytest --durations=10

pytest-k:
	@echo "Running Pytest (Keyword Search)"
	@echo "Usage: make pytest-k K=keyword"
	@if [ -z "$(K)" ]; then \
		echo "Error: K (keyword) is required. Example: make pytest-k K=test_login"; \
		exit 1; \
	fi
	@$(VENV_ACTIVATE) && pytest -k "$(K)"

pytest-w:
	@echo "Running Pytest (Show Warnings)"
	@$(VENV_ACTIVATE) && pytest -o "addopts=--reuse-db" -W always

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

d-supervisor-logs:
	docker exec -it django_ninja_api_container tail -f /var/log/supervisor/supervisord.log

d-uvicorn-logs:
	docker exec -it django_ninja_api_container tail -f /var/log/supervisor/uvicorn.log

d-gunicorn-logs:
	docker exec -it django_ninja_api_container tail -f /var/log/supervisor/gunicorn_error.log

d-celery-logs:
	docker exec -it django_ninja_api_container tail -f /var/log/supervisor/celery_worker_0.log

d-all-logs:
	docker exec -it django_ninja_api_container sh -c "tail -f /var/log/supervisor/*.log"

d-volumes:
	@echo "Listing volumes for project 'django-ninja-ready-to-go'..."
	docker volume ls --filter label=com.docker.compose.project=django-ninja-ready-to-go

d-clean-volumes:
	@echo "Removing project volumes (if any named volumes exist)..."
	docker compose -f docker-compose.yaml down -v

d-wipe-local-data:
	@echo "Removing local data directories (bind mounts) from /var/lib/docker-data/..."
	docker run --rm -v /var/lib/docker-data:/data alpine sh -c "rm -rf /data/django_ninja_db_data /data/django_ninja_redis_data"
	@echo "Data wiped."

help:
	@echo "Available Makefile commands:"
	@echo ""
	@echo "== Development Commands =="
	@echo "  run: Run the Django development server (automatically kills port 8000 first)"
	@echo "  kill-port: Kill processes using port 8000"
	@echo "  makemigrations: Create Django database migrations"
	@echo "  migrate: Apply Django database migrations"
	@echo "  shell: Log into the Django shell"
	@echo "  shell_plus: Log into the Django Shell Plus"
	@echo "  createsuperuser: Create a superuser"
	@echo "  run_gunicorn: Run the gunicorn server"
	@echo "  run_uvicorn: Run the uvicorn server"
	@echo "  generate-docs          Generate static API documentation (Swagger, ReDoc)"
	@echo "  swagger                Generate and serve Swagger UI"
	@echo "  redoc                  Generate and serve ReDoc"
	@echo "  create-app APP=name    Create a new Django Ninja app with v1 structure"
	@echo ""
	@echo "== Setup & Installation =="
	@echo "  init: Initialize the venv and install the requirements"
	@echo "  install: Install all dependencies from compiled requirements"
	@echo ""
	@echo "== Dependency Management (uv.lock workflow) =="
	@echo "  add-package: Add a package to production dependencies and update uv.lock"
	@echo "      Usage: make add-package PACKAGE=requests [VERSION=2.31.0]"
	@echo "  add-dev-package: Add a package to dev dependencies and update uv.lock"
	@echo "      Usage: make add-dev-package PACKAGE=pytest [VERSION=8.3.3]"
	@echo "  remove-package: Remove a package from production dependencies"
	@echo "      Usage: make remove-package PACKAGE=requests"
	@echo "  remove-dev-package: Remove a package from dev dependencies"
	@echo "      Usage: make remove-dev-package PACKAGE=pytest"
	@echo "  compile-deps: Lock dependencies from pyproject.toml without upgrading"
	@echo "  update-deps: Upgrade all dependencies to latest and update uv.lock"
	@echo "  package-sync: Alias for update-deps (upgrade + lock + sync)"
	@echo "  export-requirements: Export uv.lock to requirements.txt format (for CI/CD)"
	@echo "  install-legacy: Install using old requirements.txt files (deprecated)"
	@echo ""
	@echo "== Testing & Quality =="
	@echo "  isort_check: Run isort check"
	@echo "  black_check: Run black check"
	@echo "  flake8: Run flake8 check"
	@echo "  static-tests: Run isort, black, and flake8 checks"
	@echo "  pytest: Run all tests with coverage report (default)"
	@echo "  pytest-v: Run tests in verbose mode (more details)"
	@echo "  pytest-q: Run tests in quiet mode (less output)"
	@echo "  pytest-lf: Run only the last failed tests"
	@echo "  pytest-x: Stop testing after the first failure"
	@echo "  pytest-slow: Show the 10 slowest tests"
	@echo "  pytest-k K=term: Run tests matching the keyword 'term'"
	@echo "  pytest-w: Run tests and display all warnings"
	@echo "  pytest-open-report: Open the HTML coverage report in browser"
	@echo ""
	@echo "== Docker Commands =="
	@echo "  d-shell: Log into the Django container shell"
	@echo "  d-db: Start the Django database"
	@echo "  d-redis: Start the Redis service"
	@echo "  d-db-logs: Show the Django database logs"
	@echo "  d-redis-logs: Show the Redis logs"
	@echo "  d-db-and-redis: Start the Django database and Redis service"
	@echo "  d-db-and-redis-down: Stop the Django database and Redis service"
	@echo "  d-db-and-redis-restart: Restart the Django database and Redis service"
	@echo "  d-up: Start all services"
	@echo "  d-down: Stop all services"
	@echo "  d-restart: Restart all services"
	@echo "  d-logs: Show the logs"
	@echo "  d-ps: Show the running services"
	@echo "  d-build: Build the services"
	@echo "  d-pull: Pull the services"
	@echo "  d-push: Push the services"
	@echo "  d-exec: Execute a command in the services"
	@echo "  d-supervisor-logs: Show Supervisor logs"
	@echo "  d-uvicorn-logs: Show Uvicorn logs"
	@echo "  d-gunicorn-logs: Show Gunicorn logs"
	@echo "  d-celery-logs: Show Celery logs (worker 0)"
	@echo "  d-all-logs: Show all Supervisor logs"
	@echo "  d-volumes: List Docker volumes for this project"
	@echo "  d-clean-volumes: Remove Docker volumes for this project (down -v)"
	@echo "  d-wipe-local-data: Wipe local data directories (bind mounts)"
	@echo "  test-api: Run API test suite"
	@echo "  help: Show this help message"

.PHONY: run makemigrations migrate shell shell_plus createsuperuser run_gunicorn init install update-deps package-sync isort_check black_check flake8 static-tests pytest-run dynamic-test run-tests pytest pytest-v pytest-q pytest-lf pytest-x pytest-slow pytest-k pytest-w pytest-open-report test-report test-api d-shell d-db d-redis d-db-logs d-redis-logs d-db-and-redis d-db-and-redis-down d-db-and-redis-restart d-up d-down d-restart d-logs d-ps d-build d-pull d-push d-exec d-supervisor-logs d-uvicorn-logs d-gunicorn-logs d-celery-logs d-all-logs d-volumes d-clean-volumes d-wipe-local-data help generate-docs swagger redoc
