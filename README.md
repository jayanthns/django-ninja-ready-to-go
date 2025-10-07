## **Django Ninja POC**

### **Project Structure**
```bash
<project-root>/
│── docker/                  # Docker-related files
│── env/                     # Environment variables
│── requirements/            # Dependency files
│── src/                     # Django project lives inside `src`
│   ├── manage.py            # Entry point for Django commands
│   ├── main/                # Django settings, ASGI/WSGI, and core apps
│   │   ├── asgi.py          # ASGI application entry point (for Uvicorn)
│   │   ├── wsgi.py          # WSGI application entry point (for Gunicorn)
│   │   ├── settings.py      # Django settings module
│   │   ├── urls.py          # Main URL configurations
│   │   ├── __init__.py
│   ├── apps/                # Django apps
│── tests/                   # Test suite
│── Makefile                 # Makefile for quick commands
│── pyproject.toml           # Project dependencies
│── README.md                # Project documentation
```

---

## **Prerequisites**
- `Python 3.x`
- `Django`
- `Django Rest Framework`
- `Django-Ninja`
- `PostgreSQL` *(optional for local development)*

---

## **Getting Started**

### **1. Clone this repository**
```bash
git clone <placeholder link>
```

### **2. Navigate to the project directory**
```bash
cd <folder-name>
```

### **3. Create a virtual environment and install dependencies**
#### **Manually**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **Using Makefile**
```bash
make init
```

### **4. Set up environment variables**
Create a `.env` file and copy the contents from `.env.copy` to `.env`.

---

## **Running the Project**
### **Run Django (via manage.py)**
Since `manage.py` is inside `src/`, you must run it like this:
```bash
cd src
python manage.py runserver
```
Or using Makefile:
```bash
make run_django
```

### **Run Uvicorn (ASGI Server)**
Since your ASGI app is inside `src/main/asgi.py`, ensure you're in the correct directory:
```bash
cd src
uvicorn main.asgi:application --host 0.0.0.0 --port 8000 --reload
```
Or using Makefile:
```bash
make run_uvicorn
```

### **Run Celery**
Since `main` is your Django project, use it as the Celery app:
```bash
cd src
celery -A main worker --loglevel=info
```
Or using Makefile:
```bash
make run_celery
```

### **Run with Docker**
```bash
make run_docker_compose
```

---

## **📱 Apps Overview**

This project includes several Django apps demonstrating different aspects of Django Ninja development:

### **🐾 Animals App** (`apps/animals_app/`)
A complete CRUD application for managing animal records with async operations, demonstrating:
- Django Ninja API endpoints
- Async views and services
- Pydantic schemas for validation
- Database models and migrations
- Admin interface integration

### **👥 Users App** (`apps/users_app/`)
User management system with authentication features:
- User registration and management
- JWT authentication (planned)
- User profiles and permissions
- Admin interface for user management

### **🏓 Ping App** (`apps/ping_app/`)
Comprehensive health check and monitoring system:
- **Database Health Checks**: PostgreSQL connectivity, read/write permissions
- **Redis Health Checks**: Cache connectivity and operations
- **External Endpoint Pinging**: HTTP endpoint testing with aiohttp
- **System Health Aggregation**: Overall system status monitoring
- **Performance Analytics**: Response time tracking and statistics
- **Admin Interface**: Django admin integration for monitoring

📖 **[Read the complete Ping App documentation](src/apps/ping_app/README.md)** for detailed API endpoints, usage examples, and configuration.

### **🔧 Common Utilities** (`common/`)
Shared utilities and middleware:
- **Trace ID Middleware**: Request tracing with unique identifiers
- **Logger Helper**: Contextual logging with trace_id and correlation_id
- **Base Schemas**: Common Pydantic schemas for API responses
- **Background Tasks**: Async task processing examples

---

### 🎉 **Happy Coding!**
