# Ping App - Health Check & Monitoring System

![Django](https://img.shields.io/badge/Django-4.2+-092E20?logo=django&logoColor=white) ![Django Ninja](https://img.shields.io/badge/Django%20Ninja-API-FF6B6B?logo=fastapi&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-336791?logo=postgresql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-7.x-DC382D?logo=redis&logoColor=white) ![aiohttp](https://img.shields.io/badge/aiohttp-Async%20HTTP-2C5F2D?logo=python&logoColor=white)

The **Ping App** is a comprehensive health check and monitoring system for Django Ninja applications. It provides extensive connectivity testing, performance monitoring, and system health validation for databases, Redis cache, and external endpoints.

## 🎯 Purpose & Features

### Core Functionality
- **Database Health Checks**: Comprehensive PostgreSQL connectivity, read/write permissions, and performance monitoring
- **Redis Health Checks**: Cache connectivity, read/write operations, and Redis server information
- **External Endpoint Pinging**: HTTP endpoint testing with configurable methods, headers, and timeouts
- **System Health Aggregation**: Overall system status with detailed service breakdowns
- **Performance Analytics**: Response time tracking, success rates, and historical statistics
- **Comprehensive Logging**: Full request tracing with trace_id and correlation_id support

### Key Benefits
- **Production Ready**: Robust error handling and comprehensive health validation
- **Async Support**: Full async/await support for high-performance operations
- **Trace Integration**: Seamless integration with the project's logging and tracing system
- **Admin Interface**: Django admin integration for monitoring and management
- **Extensible**: Easy to add new health check types and monitoring capabilities

## 📁 App Structure

```
src/apps/ping_app/
├── v1/
│   ├── __init__.py
│   ├── admin.py          # Django admin configuration
│   ├── apps.py           # App configuration
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   ├── services.py       # Business logic
│   ├── views.py          # Main router and system health endpoints
│   ├── cache_views.py    # Redis/cache health check endpoints
│   ├── database_views.py # Database health check endpoints
│   ├── external_views.py # External endpoint pinging endpoints
│   ├── tests.py          # Test cases
│   └── urls.py           # URL routing (if needed)
└── README.md             # This documentation
```

## 🗄️ Database Models

### PingLog Model
Stores external endpoint ping results and performance metrics.

```python
class PingLog(models.Model):
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time_ms = models.FloatField()
    success = models.BooleanField()
    error_message = models.TextField(blank=True, null=True)
    request_headers = models.JSONField(default=dict, blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### SystemHealth Model
Tracks system health check results and service status.

```python
class SystemHealth(models.Model):
    service_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=[
        ('database', 'Database'),
        ('redis', 'Redis'),
        ('external_api', 'External API'),
        ('file_system', 'File System'),
    ])
    is_healthy = models.BooleanField()
    response_time_ms = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)
```

## 🚀 API Endpoints

The ping app provides a well-organized API structure with separate endpoints for different types of health checks:

```
/api/v1/pings/
├── /                    # Basic ping endpoint
├── /health/            # Overall system health
├── /cache/             # Redis health checks
├── /db/                # Database health checks
└── /external/          # External endpoint pinging
```

### Base Ping Endpoints

#### `GET /api/v1/pings/`
Basic connectivity test for the ping service itself.

**Response:**
```json
{
  "data": {
    "message": "pong",
    "status": "healthy"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/health/`
Comprehensive system health check covering all services.

**Response:**
```json
{
  "data": {
    "overall_status": "healthy",
    "services": [
      {
        "service_name": "Database",
        "service_type": "database",
        "is_healthy": true,
        "response_time_ms": 12.34,
        "error_message": null,
        "metadata": {
          "connection_count": 5,
          "database_name": "myapp_db"
        }
      },
      {
        "service_name": "Redis",
        "service_type": "redis",
        "is_healthy": true,
        "response_time_ms": 2.45,
        "error_message": null,
        "metadata": {
          "redis_version": "7.0.0",
          "memory_usage": "2.1M",
          "connected_clients": 3
        }
      }
    ],
    "checked_at": "2025-01-07T10:30:00Z",
    "uptime_seconds": null
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

### Database Health Checks (`/api/v1/pings/db/`)

#### `GET /api/v1/pings/db/ping`
Comprehensive database health check with read/write permission testing.

**Response:**
```json
{
  "data": {
    "is_healthy": true,
    "response_time_ms": 12.34,
    "error_message": null,
    "connection_count": 5,
    "database_name": "myapp_db"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/db/read`
Test database read access (SELECT operations).

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "message": "Database read successful",
    "timestamp": "uuid-string"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/db/write`
Test database write access (INSERT/UPDATE/DELETE operations).

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "message": "Database write successful",
    "timestamp": "uuid-string"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/db/ddl`
Test database DDL operations (CREATE/DROP/ALTER).

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "message": "Database DDL successful",
    "timestamp": "uuid-string"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/db/info`
Get comprehensive database information and status.

**Response:**
```json
{
  "data": {
    "is_healthy": true,
    "response_time_ms": 12.34,
    "error_message": null,
    "connection_count": 5,
    "database_name": "myapp_db"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/db/tables`
List all tables in the current database.

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "total_tables": 3,
    "tables": [
      {
        "name": "animals_app_animal",
        "type": "BASE TABLE",
        "rows": 5,
        "size_mb": 0.1
      }
    ]
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `POST /api/v1/pings/db/test-write/`
Test database write permissions specifically (POST endpoint).

**Response:**
```json
{
  "data": {
    "success": true,
    "error_message": null,
    "timestamp": "uuid-string"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `POST /api/v1/pings/db/test-read/`
Test database read permissions specifically (POST endpoint).

**Response:**
```json
{
  "data": {
    "success": true,
    "error_message": null,
    "timestamp": "uuid-string"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

### Redis Health Checks (`/api/v1/pings/cache/`)

#### `GET /api/v1/pings/cache/`
Comprehensive Redis health check with read/write permission testing.

**Response:**
```json
{
  "data": {
    "is_healthy": true,
    "response_time_ms": 2.45,
    "error_message": null,
    "redis_version": "7.0.0",
    "memory_usage": "2.1M",
    "connected_clients": 3
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/cache/info`
Get cache service information and statistics.

**Response:**
```json
{
  "data": {
    "is_healthy": true,
    "response_time_ms": 2.45,
    "error_message": null,
    "redis_version": "7.0.0",
    "memory_usage": "2.1M",
    "connected_clients": 3
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/cache/keys`
Get cache keys matching a pattern.

**Query Parameters:**
- `pattern` (optional): Key pattern to match (default: "*")
- `limit` (optional): Maximum number of keys to return (default: 100)

**Response:**
```json
{
  "data": {
    "cache_type": "Redis",
    "use_redis": true,
    "pattern": "*",
    "total_keys": 10,
    "safe_keys": 8,
    "sensitive_keys_filtered": 2,
    "returned_keys": 8,
    "limit": 100,
    "keys": [
      {
        "key": "key_1",
        "type": "string",
        "ttl": null,
        "ttl_human": "no expiration"
      }
    ],
    "status": "healthy"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `POST /api/v1/pings/cache/test-write/`
Test Redis write permissions specifically.

**Response:**
```json
{
  "data": {
    "success": true,
    "error_message": null,
    "test_type": "redis_write",
    "timestamp": "uuid-string"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `POST /api/v1/pings/cache/test-read/`
Test Redis read permissions specifically.

**Response:**
```json
{
  "data": {
    "success": true,
    "error_message": null,
    "test_type": "redis_read",
    "timestamp": "uuid-string"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

### External Endpoint Pinging (`/api/v1/pings/external/`)

#### `GET /api/v1/pings/external/`
Basic status endpoint for the external ping service.

**Response:**
```json
{
  "data": {
    "message": "external ping service ready",
    "status": "healthy"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `POST /api/v1/pings/external/endpoint/`
Ping external HTTP endpoints with configurable parameters.

**Request Body:**
```json
{
  "endpoint": "https://httpbin.org/get",
  "method": "GET",
  "headers": {
    "User-Agent": "Django-Ninja-Ping/1.0"
  },
  "timeout": 10
}
```

**Response:**
```json
{
  "data": {
    "endpoint": "https://httpbin.org/get",
    "method": "GET",
    "status_code": 200,
    "response_time_ms": 245.67,
    "success": true,
    "error_message": null,
    "response_headers": {
      "content-type": "application/json",
      "content-length": "1234"
    }
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/external/logs/`
Retrieve recent ping logs with optional limit.

**Query Parameters:**
- `limit` (optional): Maximum number of logs to return (default: 100)

**Response:**
```json
{
  "data": [
    {
      "endpoint": "https://httpbin.org/get",
      "method": "GET",
      "status_code": 200,
      "response_time_ms": 245.67,
      "success": true,
      "error_message": null,
      "response_headers": {
        "content-type": "application/json"
      }
    }
  ],
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/external/stats/`
Get comprehensive ping statistics and analytics.

**Response:**
```json
{
  "data": {
    "total_pings": 150,
    "successful_pings": 142,
    "failed_pings": 8,
    "average_response_time_ms": 234.56,
    "min_response_time_ms": 45.23,
    "max_response_time_ms": 1234.56,
    "last_24h_pings": 45,
    "last_24h_successful": 43,
    "last_24h_success_rate": 95.56
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

#### `GET /api/v1/pings/external/health/`
Get external ping service health status.

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "message": "External ping service is operational",
    "recent_success_rate": 95.56,
    "last_check": "2025-01-07T10:30:00Z"
  },
  "trace_id": "uuid-string",
  "error": {}
}
```

## 🔧 Services Architecture

### PingService
Handles external endpoint pinging and analytics.

**Key Methods:**
- `ping_endpoint()`: Ping external endpoints with aiohttp
- `get_ping_logs()`: Retrieve ping history
- `get_ping_stats()`: Calculate performance statistics
- `log_ping_result()`: Store ping results in database

### DatabaseHealthService
Comprehensive database health monitoring.

**Key Methods:**
- `check_database_health()`: Full database connectivity check
- `test_database_read()`: Test read permissions
- `test_database_write()`: Test write permissions

### RedisHealthService
Redis cache health monitoring and testing.

**Key Methods:**
- `check_redis_health()`: Full Redis connectivity check
- `test_redis_read()`: Test read operations
- `test_redis_write()`: Test write operations

### SystemHealthService
Aggregates health status from all services.

**Key Methods:**
- `get_overall_health()`: Comprehensive system health check
- `log_health_check()`: Store health check results

## 📊 Pydantic Schemas

### Request Schemas

#### PingRequestSchema
```python
class PingRequestSchema(BaseModel):
    endpoint: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    timeout: int = 10
```

### Response Schemas

#### PingResponseSchema
```python
class PingResponseSchema(BaseModel):
    id: Optional[int] = None
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    request_headers: Optional[Dict[str, str]] = None
    response_headers: Optional[Dict[str, str]] = None
    created_at: Optional[datetime] = None
```

#### HealthCheckResponseSchema
```python
class HealthCheckResponseSchema(BaseModel):
    overall_status: str
    services: List[ServiceHealthSchema]
    checked_at: datetime
    uptime_seconds: Optional[int] = None
```

## 🧪 Testing

The ping app includes comprehensive test coverage:

```bash
# Run ping app tests
python manage.py test apps.ping_app.v1.tests

# Run specific test classes
python manage.py test apps.ping_app.v1.tests.PingServiceTest
python manage.py test apps.ping_app.v1.tests.DatabaseHealthServiceTest
python manage.py test apps.ping_app.v1.tests.RedisHealthServiceTest
```

### Test Coverage
- **PingService**: External endpoint testing, logging, and statistics
- **DatabaseHealthService**: Database connectivity and permission testing
- **RedisHealthService**: Redis connectivity and operation testing
- **SystemHealthService**: Overall health aggregation
- **Models**: Database model validation and relationships

## 🔍 Django Admin Integration

The ping app provides comprehensive Django admin interfaces:

### PingLog Admin
- List view with filtering by method, status code, and success
- Search by endpoint and error messages
- Detailed fieldsets for request/response information
- Read-only timestamp fields

### SystemHealth Admin
- List view with filtering by service type and health status
- Search by service name and error messages
- Detailed fieldsets for service information and metadata
- Read-only timestamp fields

## 🚀 Usage Examples

### Basic Health Check
```python
# Check overall system health
response = await SystemHealthService.get_overall_health()
print(f"System status: {response.overall_status}")
```

### External Endpoint Monitoring
```python
# Ping external service
ping_request = PingRequestSchema(
    endpoint="https://api.example.com/health",
    method="GET",
    timeout=5
)
result = await PingService.ping_endpoint(ping_request)
print(f"Response time: {result.response_time_ms}ms")
```

### Database Health Monitoring
```python
# Check database health
db_health = await DatabaseHealthService.check_database_health()
if not db_health.is_healthy:
    print(f"Database issue: {db_health.error_message}")
```

### Redis Health Monitoring
```python
# Check Redis health
redis_health = await RedisHealthService.check_redis_health()
print(f"Redis version: {redis_health.redis_version}")
```

## 🔧 Configuration

### Environment Variables
```bash
# Database configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis configuration
REDIS_URL=redis://localhost:6379/0

# Logging configuration
LOG_LEVEL=INFO
```

### Django Settings
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    "apps.ping_app.v1",
]

# URL configuration
urlpatterns = [
    # ... other patterns
    path("api/ping/", include("apps.ping_app.v1.urls")),
]
```

## 📈 Performance Considerations

### Async Operations
- All services use async/await for optimal performance
- Database operations use `sync_to_async` for Django ORM compatibility
- External HTTP requests use `aiohttp` for concurrent operations

### Caching Strategy
- Health check results can be cached to reduce database load
- Redis health checks include connection pooling information
- Response time tracking for performance monitoring

### Error Handling
- Comprehensive exception handling for all external dependencies
- Graceful degradation when services are unavailable
- Detailed error messages for debugging

## 🔒 Security Features

### Input Validation
- Pydantic schemas for request validation
- URL validation for external endpoints
- Timeout limits to prevent hanging requests

### Data Protection
- Sensitive information filtering in logs
- Secure error message handling
- Request/response header sanitization

### Access Control
- Integration with Django's authentication system
- Admin interface permissions
- API endpoint access control

## 🚀 Deployment Considerations

### Production Setup
- Configure proper database connection pooling
- Set up Redis clustering for high availability
- Implement health check monitoring and alerting
- Configure log aggregation and monitoring

### Monitoring Integration
- Integration with monitoring systems (Prometheus, Grafana)
- Health check endpoints for load balancers
- Performance metrics collection
- Alert configuration for service failures

## 📚 Dependencies

### Core Dependencies
- `django`: Web framework
- `django-ninja`: API framework
- `aiohttp`: Async HTTP client
- `pydantic`: Data validation
- `psycopg2`: PostgreSQL adapter

### Optional Dependencies
- `redis`: Redis client (if using Redis caching)
- `celery`: Background task processing

## 🤝 Contributing

### Adding New Health Checks
1. Create new service class in `services.py`
2. Add corresponding schemas in `schemas.py`
3. Implement API endpoints in `views.py`
4. Add test cases in `tests.py`
5. Update admin configuration if needed

### Code Style
- Follow Django and Python best practices
- Use type hints throughout
- Maintain comprehensive test coverage
- Document all public methods and classes

## 📄 License

This ping app is part of the Django Ninja Ready-to-Go project and follows the same licensing terms.

---

**Note**: This ping app is designed to be production-ready and provides comprehensive health monitoring capabilities for Django Ninja applications. It integrates seamlessly with the project's logging, tracing, and admin systems.
