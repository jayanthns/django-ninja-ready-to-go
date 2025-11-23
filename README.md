# 🚀 Django Ninja Ready-to-Go

![Django](https://img.shields.io/badge/Django-4.2+-092E20?logo=django&logoColor=white) ![Django Ninja](https://img.shields.io/badge/Django%20Ninja-API-FF6B6B?logo=fastapi&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-336791?logo=postgresql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-7.x-DC382D?logo=redis&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)

A **production-ready Django Ninja API framework** with comprehensive health monitoring, advanced logging, request tracing, and modern development practices. This project serves as a complete template for building scalable Django Ninja applications with enterprise-grade features.

## 🎯 **Key Features**

- **🏗️ Modern Architecture**: Django Ninja with async support, structured apps, and clean separation of concerns
- **🔍 Advanced Logging**: Request tracing with `trace_id` and `correlation_id`, contextual logging, and structured JSON logs
- **🏥 Health Monitoring**: Comprehensive health checks for databases, Redis, external services, and system status
- **🐳 Docker Ready**: Complete Docker setup with multi-stage builds, development and production configurations
- **⚡ Performance**: Async views, background tasks, and optimized database operations
- **🛡️ Production Ready**: Security best practices, error handling, monitoring, and deployment scripts
- **📊 Admin Interface**: Rich Django admin integration for all models and monitoring
- **🧪 Testing**: Comprehensive test coverage with async test support
- **🔧 Developer Experience**: Makefile automation, hot reload, and development tools

---

## 🎯 **Using This Template**

This repository is designed to be a **production-ready template** for your Django Ninja projects. You can use it in two ways:

### **Option 1: Use as GitHub Template (Recommended)**

Click the **"Use this template"** button on GitHub to create a new repository with this structure:

1. Go to [https://github.com/jayanthns/django-ninja-ready-to-go](https://github.com/jayanthns/django-ninja-ready-to-go)
2. Click the green **"Use this template"** button
3. Choose **"Create a new repository"**
4. Name your new project
5. Clone your new repository:

   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_PROJECT_NAME.git
   cd YOUR_PROJECT_NAME
   ```

### **Option 2: Clone and Customize**

Clone this repository directly and customize it:

```bash
# Clone the template
git clone https://github.com/jayanthns/django-ninja-ready-to-go.git my-project
cd my-project

# Remove the original git history (optional)
rm -rf .git
git init
git add .
git commit -m "Initial commit from django-ninja-ready-to-go template"

# Add your own remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_PROJECT_NAME.git
git push -u origin main
```

### **📝 Getting Started with Your New Project**

After creating your project from the template:

1. **Initialize the environment:**

   ```bash
   make init
   ```

2. **Customize the project:**
   - [ ] Update `pyproject.toml` with your project name and details
   - [ ] Rename apps in `apps/` to match your domain (optional)
   - [ ] Update `.env.example` with your configuration
   - [ ] Modify `main/settings/base.py` for your needs

3. **Set up your database:**

   ```bash
   # Create .env file
   cp .env.example .env

   # Edit .env with your database credentials
   # Then run migrations
   make migrate
   ```

4. **Create a superuser:**

   ```bash
   make createsuperuser
   ```

5. **Start developing:**

   ```bash
   make run
   # Open http://localhost:8000/api/docs
   ```

### **🔄 Integrating into Existing Django Project**

If you have an existing Django project and want to use parts of this template:

#### **1. Copy the Logging System**

```bash
# Copy these files to your project:
cp common/middleware.py YOUR_PROJECT/common/
cp common/logger_helper.py YOUR_PROJECT/common/
cp main/settings/logging.py YOUR_PROJECT/main/settings/
```

Then add to `settings.py`:

```python
MIDDLEWARE = [
    'common.middleware.TraceIDMiddleware',  # Add this
    # ... other middleware
]
```

#### **2. Copy the Health Monitoring App**

```bash
# Copy the entire ping app
cp -r apps/ping_app YOUR_PROJECT/apps/

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'apps.ping_app.v1',
]

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

#### **3. Use the Package Management Setup**

```bash
# Copy these files:
cp pyproject.toml YOUR_PROJECT/
cp Makefile YOUR_PROJECT/
cp PACKAGE_MANAGER.md YOUR_PROJECT/

# Initialize uv and install dependencies
make init
```

#### **4. Copy Specific Features**

**Async CRUD Pattern (from Animals App):**

- Copy `apps/animals_app/v1/services.py` as reference
- Copy `apps/animals_app/v1/schemas.py` for Pydantic patterns
- Copy `apps/animals_app/v1/views.py` for async endpoint examples

**User Management (from Users App):**

- Copy `apps/users_app/` for complete user system
- Includes password hashing, validation, and async operations

---

## 📁 **Project Structure**

```bash
django-ninja-ready-to-go/
├── 📄 manage.py                 # Django management script
├── 📁 main/                     # Core Django configuration
│   ├── 📁 settings/             # Environment-specific settings
│   │   ├── base.py              # Base settings
│   │   ├── db.py                # Database configuration
│   │   └── logging.py           # Logging configuration
│   ├── asgi.py                  # ASGI application (Uvicorn)
│   ├── wsgi.py                  # WSGI application (Gunicorn)
│   └── urls.py                  # Main URL routing
├── 📁 apps/                     # Django applications
│   ├── 📁 animals_app/          # CRUD example with async operations
│   ├── 📁 users_app/            # User management system
│   └── 📁 ping_app/             # Health monitoring & external pinging
├── 📁 common/                   # Shared utilities and middleware
│   ├── middleware.py            # Trace ID middleware
│   ├── logger_helper.py         # Contextual logging system
│   ├── base_schemas.py          # Common Pydantic schemas
│   └── background_tasks.py      # Async task examples
├── 📁 utils/                    # Helper utilities
├── 📁 deploy/                   # Deployment scripts and configurations
│   ├── 📁 db_scripts/           # Database initialization
│   ├── 📁 entrypoint_scripts/   # Container entrypoints
│   ├── 📁 shell_scripts/        # Service startup scripts
│   └── 📁 supervisor_scripts/   # Process management
├── 📁 requirements/             # Python dependencies
├── 📁 requirements_raw/         # Raw dependency specifications
├── 📁 tests/                    # Test suite
├── 📄 docker-compose.yaml       # Multi-service Docker setup
├── 📄 Dockerfile                # Production Docker image
├── 📄 Dockerfile-local          # Development Docker image
├── 📄 Makefile                  # Development automation
├── 📄 PACKAGE_MANAGER.md        # Package management guide
├── 📄 pyproject.toml            # Project metadata
├── 📄 uv.lock                   # Dependency lock file
└── 📄 README.md                 # This documentation
```

---

## 🛠️ **Prerequisites**

- **Python 3.10+** (recommended 3.12)
- **PostgreSQL 16** (for production)
- **Redis 7.x** (for caching and health checks)
- **Docker & Docker Compose** (for containerized development)
- **Git** (for version control)

## 🚀 **Quick Start**

### **Option 1: Docker (Recommended)**

```bash
# Clone the repository
git clone <your-repo-url>
cd django-ninja-ready-to-go

# Start all services with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:8000
```

### **Option 2: Local Development**

```bash
# Clone the repository
git clone <your-repo-url>
cd django-ninja-ready-to-go

# Initialize the project (creates venv and installs dependencies)
make init

# Set up environment variables
cp .env.example .env  # Edit as needed

# Run database migrations
make migrate

# Start the development server
make run

# Access the application
open http://localhost:8000
```

---

## 📦 **Package Management**

This project uses **`uv`** - a fast, modern Python package manager (10-100x faster than pip!).

### Quick Commands

```bash
# Install all dependencies
make install

# Add a new package
make add-package PACKAGE=requests VERSION=2.31.0

# Update all packages
make update-deps
```

### 📚 Complete Guide

**New to package management or want to know how we use `uv` in this project?**

👉 **[Read the Complete Package Manager Guide](PACKAGE_MANAGER.md)** - Beginner-friendly guide covering:

- What is `uv` and why we use it
- How to add/remove packages
- Manual package addition exercises
- Troubleshooting and FAQ
- Best practices for this Django Ninja project

---

## 🏗️ **Project Applications**

## 🔧 **Development Commands**

The project includes a comprehensive Makefile for common development tasks:

### **Server Management**

```bash
make run              # Start Django development server
make run_uvicorn      # Start with Uvicorn (Development-ready ASGI)
make run_gunicorn     # Start with Gunicorn (Production-ready ASGI)
make kill-port        # Kill processes on port 8000
```

### **Database Operations**

```bash
make makemigrations   # Create new migrations
make migrate          # Apply migrations
make shell            # Django shell
make shell_plus       # Django shell with extensions
make createsuperuser  # Create admin user
```

### **Docker Operations**

```bash
make d-build          # Build Docker services
make d-up             # Start all services (detached)
make d-down           # Stop all services
make d-logs           # Show logs
make d-shell          # Shell into API container
```

### **Development Tools**

```bash
make init             # Initialize project (venv + dependencies)
make install          # Install dependencies
make test             # Run tests
make lint             # Run code linting
make format           # Format code
```

## 🌐 **API Documentation**

Once the server is running, you can access:

- **📚 Interactive API Docs**: <http://localhost:8000/api/docs>
- **📋 OpenAPI Schema**: <http://localhost:8000/api/openapi.json>
- **🔧 Django Admin**: <http://localhost:8000/admin/>

## 🏗️ **Architecture Overview**

### **Core Components**

#### **🔍 Advanced Logging & Tracing**

- **Trace ID Middleware**: Automatically generates unique `trace_id` for each request
- **Correlation ID Support**: For distributed tracing across services
- **Contextual Logging**: Request-specific logger with automatic context injection
- **Structured JSON Logs**: Production-ready logging with consistent format
- **Background Task Integration**: Seamless logging in async tasks

#### **🏥 Health Monitoring System**

- **Database Health**: PostgreSQL connectivity, read/write permissions, DDL operations
- **Redis Health**: Cache connectivity, operations testing, server information
- **External Service Monitoring**: HTTP endpoint pinging with aiohttp
- **System Health Aggregation**: Overall status with detailed service breakdowns
- **Performance Analytics**: Response time tracking and success rate monitoring

#### **⚡ Async-First Design**

- **Async Views**: Full async/await support for high performance
- **Background Tasks**: Celery integration for long-running operations
- **Database Operations**: Optimized async database queries
- **HTTP Clients**: aiohttp for external service communication

---

## 📱 **Applications Overview**

The project includes three comprehensive Django applications demonstrating different aspects of Django Ninja development:

### **🐾 Animals App** (`apps/animals_app/`)

A complete CRUD application showcasing modern Django Ninja patterns.

👉 **[Read the Animals App Documentation](apps/animals_app/README.md)**

**Features:**

- **Async CRUD Operations**: Create, read, update, delete with async/await
- **Pydantic Schemas**: Request/response validation with detailed schemas
- **Service Layer**: Clean separation of business logic
- **Admin Integration**: Rich Django admin interface
- **Logger Integration**: Demonstrates contextual logging usage

**API Endpoints:**

```bash
GET    /api/v1/animals/           # List all animals
POST   /api/v1/animals/           # Create new animal
GET    /api/v1/animals/{id}/      # Get specific animal
PUT    /api/v1/animals/{id}/      # Update animal
DELETE /api/v1/animals/{id}/      # Delete animal
GET    /api/v1/animals/logger-demo/ # Logger demonstration
```

### **👥 Users App** (`apps/users_app/`)

User management system with authentication and profile features.

👉 **[Read the Users App Documentation](apps/users_app/README.md)**

**Features:**

- **User Registration**: Complete user signup flow with password hashing
- **Profile Management**: User retrieval by ID
- **Secure Passwords**: Django's built-in password hashing (PBKDF2)
- **Email Validation**: Pydantic EmailStr validation
- **Async Operations**: Full async/await support

**API Endpoints:**

```bash
POST   /api/v1/users/register      # Register new user
GET    /api/v1/users/{id}/          # Get user profile
DELETE /api/v1/users/{id}/        # Delete user
```

### **🏓 Ping App** (`apps/ping_app/`)

Comprehensive health check and monitoring system with organized API structure.

👉 **[Read the Ping App Documentation](apps/ping_app/README.md)**

**Features:**

- **Database Health Checks**: PostgreSQL connectivity, read/write permissions, DDL operations, table listing
- **Redis Health Checks**: Cache connectivity, read/write operations, key management, server info
- **External Endpoint Pinging**: HTTP endpoint testing with aiohttp, logs, and statistics
- **System Health Aggregation**: Overall system status monitoring with detailed service breakdowns
- **Performance Analytics**: Response time tracking, success rates, and historical statistics
- **Admin Interface**: Django admin integration for monitoring and management

**API Structure:**

```bash
/api/v1/pings/
├── /                    # Basic ping endpoint
├── /health/            # Overall system health
├── /cache/             # Redis health checks
├── /db/                # Database health checks
└── /external/          # External endpoint pinging
```

**Quick Examples:**

```bash
# Basic ping
curl http://localhost:8000/api/v1/pings/

# System health check
curl http://localhost:8000/api/v1/pings/health/

# Database health
curl http://localhost:8000/api/v1/pings/db/ping

# Redis health
curl http://localhost:8000/api/v1/pings/cache/

# External endpoint ping
curl -X POST http://localhost:8000/api/v1/pings/external/endpoint/ \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "https://httpbin.org/get", "method": "GET"}'

# Ping logs and statistics
curl http://localhost:8000/api/v1/pings/external/logs/
curl http://localhost:8000/api/v1/pings/external/stats/
```

### **🔧 Common Utilities** (`common/`)

Shared utilities and middleware providing enterprise-grade functionality:

#### **Trace ID Middleware** (`middleware.py`)

- **Automatic Trace ID Generation**: Unique identifier for each request
- **Correlation ID Support**: For distributed tracing across services
- **Request Context Injection**: Attaches trace context to request object
- **Response Header Injection**: Adds trace headers to responses
- **Logger Integration**: Seamless integration with contextual logging

#### **Logger Helper** (`logger_helper.py`)

- **Contextual Logging**: Request-specific logger with automatic context
- **Background Task Support**: Logger context for async tasks
- **Structured Logging**: JSON-formatted logs with trace information
- **Singleton Pattern**: Thread-safe logger management
- **Context Variables**: Python ContextVar for async compatibility

#### **Base Schemas** (`base_schemas.py`)

- **Standardized API Responses**: Consistent response format across all endpoints
- **Error Handling**: Structured error response schemas
- **Trace ID Integration**: Automatic trace_id inclusion in responses
- **Type Safety**: Full Pydantic validation and type hints

#### **Background Tasks** (`background_tasks.py`)

- **Async Task Examples**: Demonstrates background task patterns
- **Logger Context Passing**: Shows how to maintain trace context in tasks
- **Task Management**: Examples of task creation and execution
- **Error Handling**: Proper error handling in background operations

## 🐳 **Docker & Deployment**

### **Docker Configuration**

- **Multi-stage Builds**: Optimized production images
- **Development & Production**: Separate Dockerfiles for different environments
- **Docker Compose**: Complete multi-service setup with PostgreSQL and Redis
- **Health Checks**: Container health monitoring
- **Volume Management**: Persistent data and development volumes

### **Deployment Scripts** (`deploy/`)

- **Database Scripts**: Schema initialization and migrations
- **Entrypoint Scripts**: Container startup and configuration
- **Shell Scripts**: Service management and startup
- **Supervisor Scripts**: Process management and monitoring

### **Production Features**

- **Environment Configuration**: Separate settings for different environments
- **Security Headers**: Production-ready security configurations
- **Logging Configuration**: Structured logging for production
- **Database Optimization**: Connection pooling and query optimization
- **Caching Strategy**: Redis integration for performance

### **Deployment Configuration**

The `deploy/` directory contains all necessary scripts for production deployment. The behavior is controlled by environment variables in `.env`:

#### **Configuration Flags**

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_SUPERVISOR` | `true` | **Enabled**: Uses Supervisor (recommended). **Disabled**: Runs Gunicorn directly (for orchestration). |
| `RUN_CELERY_TOGETHER` | `false` | **Enabled**: Runs Gunicorn and Celery together (requires Supervisor). **Disabled**: Runs only Gunicorn. |

#### **Deployment Scenarios**

1. **Standard Production (Recommended)**:
    - `USE_SUPERVISOR=true`
    - `RUN_CELERY_TOGETHER=false`
    - **Result**: The container runs Gunicorn managed by Supervisor. Celery workers should be run in separate containers using the same image but overriding the command (e.g., `celery -A main worker`).

2. **All-in-One (Low Resource)**:
    - `USE_SUPERVISOR=true`
    - `RUN_CELERY_TOGETHER=true`
    - **Result**: The container runs both Gunicorn and Celery managed by a single Supervisor instance.
    - *Note: You must uncomment the Celery section in `deploy/supervisor_scripts/supervisord.conf` to enable this.*

3. **Simple / Orchestrated**:
    - `USE_SUPERVISOR=false`
    - **Result**: The container runs Gunicorn directly as the entrypoint process. Useful if you are using Kubernetes or another orchestrator to manage process lifecycles directly.

### **Deployment Files Reference**

Here is a guide to the files in the `deploy/` directory and when to use them:

#### **1. Entrypoint Scripts (`deploy/entrypoint_scripts/`)**

These are the main entry points for the Docker container.

- **`entrypoint.sh`**: **[Primary]** The default command for the Docker image. It loads environment variables, checks the `USE_SUPERVISOR` flag, and decides whether to start Supervisor or run Gunicorn directly.
- **`gunicorn_entrypoint.sh`**: A specific entrypoint that forces the use of Supervisor with the Gunicorn configuration. Use this if you want to bypass the logic in `entrypoint.sh` and strictly run Gunicorn via Supervisor.

#### **2. Supervisor Configurations (`deploy/supervisor_scripts/`)**

Configuration files for Supervisor, which manages processes inside the container.

- **`supervisord.conf`**: **[Primary]** The main configuration file used when `RUN_CELERY_TOGETHER=true`. It can manage multiple processes (Gunicorn + Celery).
- **`gunicorn_supervisord.conf`**: Used when `RUN_CELERY_TOGETHER=false`. It configures Supervisor to manage *only* Gunicorn.
- **`celery_supervisord.conf`**: A standalone configuration for running Celery workers under Supervisor. Use this if you are building a dedicated Celery worker container that uses Supervisor.

#### **3. Shell Scripts (`deploy/shell_scripts/`)**

Actual startup scripts called by Supervisor or the entrypoints.

- **`gunicorn_start.sh`**: Prepares the environment (migrations, static files) and starts the Gunicorn server.
- **`celery_start.sh`**: Starts a single Celery worker instance.
- **`celery_multiple_workers_start.sh`**: Starts multiple Celery workers based on the `CELERY_WORKERS` environment variable.

#### **4. Database Scripts (`deploy/db_scripts/`)**

- **`init_schema.sh`**: Helper script to initialize the database schema, often used in CI/CD pipelines or initial setup.

## 🧪 **Testing & Quality**

### **Test Coverage**

- **Unit Tests**: Comprehensive test coverage for all apps
- **Async Testing**: Support for testing async views and services
- **Integration Tests**: End-to-end API testing
- **Mock Services**: External service mocking for reliable tests

### **Code Quality**

- **Type Hints**: Full type annotation throughout the codebase
- **Linting**: Code quality enforcement with flake8, black, isort
- **Documentation**: Comprehensive docstrings and API documentation
- **Error Handling**: Robust error handling and logging

## 🚀 **Performance & Monitoring**

### **Performance Features**

- **Async Operations**: Full async/await support for high concurrency
- **Database Optimization**: Efficient queries and connection management
- **Caching**: Redis integration for improved performance
- **Background Tasks**: Non-blocking operations for better responsiveness

### **Monitoring & Observability**

- **Request Tracing**: Complete request lifecycle tracking
- **Health Monitoring**: Comprehensive system health checks
- **Performance Metrics**: Response time tracking and analytics
- **Error Tracking**: Detailed error logging and monitoring
- **Admin Interface**: Rich monitoring and management interface

## 📚 **Documentation & Resources**

### **API Documentation**

- **Interactive Docs**: Swagger UI at `/api/docs`
- **OpenAPI Schema**: Machine-readable API specification
- **Code Examples**: Comprehensive usage examples
- **Error Codes**: Detailed error response documentation

### **Static Documentation**

You can generate static documentation files (Swagger UI and ReDoc) using the Makefile command:

```bash
make generate-docs
```

This will create a `docs/` directory with `swagger.html` and `redoc.html`.

**Viewing on GitHub:**
GitHub's README does not support embedding interactive JavaScript applications like Swagger UI or ReDoc directly. To view these files:

1. **Locally**: Open `docs/swagger.html` or `docs/redoc.html` in your browser.
2. **GitHub Pages**: Enable GitHub Pages for your repository (Settings -> Pages -> Source: `main` branch, `/docs` folder). Your docs will be available at:
    - `https://<username>.github.io/<repo>/swagger.html`
    - `https://<username>.github.io/<repo>/redoc.html`

### **Development Resources**

- **Makefile Commands**: Complete development automation
- **Docker Setup**: Containerized development environment
- **Environment Configuration**: Flexible configuration management
- **Deployment Guides**: Production deployment instructions

## 🤝 **Contributing**

### **Development Setup**

1. Fork the repository
2. Create a feature branch
3. Set up the development environment
4. Make your changes
5. Run tests and linting
6. Submit a pull request

### **Code Standards**

- Follow Django and Python best practices
- Use type hints throughout
- Maintain test coverage
- Document all public APIs
- Follow the existing code style

---

## 🎉 **Ready to Build Amazing APIs!**

This Django Ninja Ready-to-Go template provides everything you need to build production-ready APIs with modern Python practices. From advanced logging and health monitoring to Docker deployment and comprehensive testing, it's designed to scale with your application needs.

## Happy Coding! 🚀
