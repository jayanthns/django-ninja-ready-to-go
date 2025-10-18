from datetime import datetime
from typing import Any, Dict, List, Optional

from ninja import Schema


class PingLogSchema(Schema):
    """Schema for ping log data."""

    id: int
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    request_headers: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}
    created_at: datetime


class PingRequestSchema(Schema):
    """Schema for ping request."""

    endpoint: str
    method: str = "GET"
    timeout: int = 5
    headers: Optional[Dict[str, str]] = None


class PingResponseSchema(Schema):
    """Schema for ping response."""

    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    response_headers: Dict[str, Any] = {}


class SystemHealthSchema(Schema):
    """Schema for system health check data."""

    id: int
    service_name: str
    service_type: str
    is_healthy: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    checked_at: datetime


class HealthCheckResponseSchema(Schema):
    """Schema for health check response."""

    service_name: str
    service_type: str
    is_healthy: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class DatabaseHealthSchema(Schema):
    """Schema for database health check."""

    is_healthy: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    connection_count: Optional[int] = None
    database_name: Optional[str] = None


class RedisHealthSchema(Schema):
    """Schema for Redis health check."""

    is_healthy: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    redis_version: Optional[str] = None
    memory_usage: Optional[str] = None
    connected_clients: Optional[int] = None
    uptime_in_seconds: Optional[int] = None
    total_commands_processed: Optional[int] = None
    evicted_keys: Optional[int] = None
    keyspace_hits: Optional[int] = None
    keyspace_misses: Optional[int] = None
    role: Optional[str] = None


class SystemStatusSchema(Schema):
    """Schema for overall system status."""

    overall_status: str  # "healthy", "degraded", "unhealthy"
    services: List[HealthCheckResponseSchema]
    checked_at: datetime
    uptime_seconds: Optional[float] = None


class PingStatsSchema(Schema):
    """Schema for ping statistics."""

    total_pings: int
    successful_pings: int
    failed_pings: int
    average_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    last_24h_pings: int
    last_24h_success_rate: float
