from django.db import models


class PingLog(models.Model):
    """Model to store ping requests and responses for database connectivity testing."""

    endpoint = models.CharField(max_length=255, help_text="The endpoint that was pinged")
    method = models.CharField(max_length=10, help_text="HTTP method used")
    status_code = models.IntegerField(help_text="HTTP status code returned")
    response_time_ms = models.FloatField(help_text="Response time in milliseconds")
    success = models.BooleanField(help_text="Whether the ping was successful")
    error_message = models.TextField(blank=True, null=True, help_text="Error message if ping failed")
    request_headers = models.JSONField(default=dict, blank=True, help_text="Request headers sent")
    response_headers = models.JSONField(default=dict, blank=True, help_text="Response headers received")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the ping was performed")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ping Log"
        verbose_name_plural = "Ping Logs"

    def __str__(self) -> str:
        return f"Ping to {self.endpoint} - {self.status_code} ({self.response_time_ms}ms)"


class SystemHealth(models.Model):
    """Model to store system health check results."""

    service_name = models.CharField(max_length=100, help_text="Name of the service being checked")
    service_type = models.CharField(
        max_length=20,
        choices=[
            ("database", "Database"),
            ("redis", "Redis"),
            ("external_api", "External API"),
            ("file_system", "File System"),
        ],
        help_text="Type of service being checked",
    )
    is_healthy = models.BooleanField(help_text="Whether the service is healthy")
    response_time_ms = models.FloatField(null=True, blank=True, help_text="Response time in milliseconds")
    error_message = models.TextField(blank=True, null=True, help_text="Error message if check failed")
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional metadata about the health check"
    )
    checked_at = models.DateTimeField(auto_now_add=True, help_text="When the health check was performed")

    class Meta:
        ordering = ["-checked_at"]
        verbose_name = "System Health Check"
        verbose_name_plural = "System Health Checks"

    def __str__(self) -> str:
        status = "Healthy" if self.is_healthy else "Unhealthy"
        return f"{self.service_name} ({self.service_type}) - {status}"
