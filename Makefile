# Detect the operating system
ifeq ($(OS),Windows_NT)
	# Windows
	VENV_ACTIVATE = .\venv\Scripts\activate
else
	# Unix-based systems (Linux/Mac)
	VENV_ACTIVATE = source ./venv/bin/activate
endif

run:
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
	@$(VENV_ACTIVATE) && cd src && uvicorn main.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --reload


# Initialize the venv and install the requirements

init:
	python3 -m pip install uv
	uv venv venv
	@$(MAKE) install


install:
	@$(VENV_ACTIVATE) && uv pip install --upgrade pip-tools pip wheel
	@$(VENV_ACTIVATE) && uv pip install --upgrade -r requirements/prod_requirements.txt -r requirements/test_requirements.txt -r requirements/dev_requirements.txt


update-deps:
	@$(VENV_ACTIVATE) && uv pip compile --upgrade --resolver backtracking -o requirements/prod_requirements.txt requirements_raw/prod_requirements.in
	@$(VENV_ACTIVATE) && uv pip compile --upgrade --resolver backtracking -o requirements/test_requirements.txt requirements_raw/test_requirements.in
	@$(VENV_ACTIVATE) && uv pip compile --upgrade --resolver backtracking -o requirements/dev_requirements.txt requirements_raw/dev_requirements.in


update: update-deps install


.PHONY: run makemigrations migrate shell createsuperuser update-deps install update init

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
	docker compose -f docker/docker-compose.yaml up --build

start_docker_compose: run_docker_compose

stop_docker_compose:
	docker compose -f docker/docker-compose.yaml down

d_shell:
	docker exec -it django_ninja_api_container /bin/bash