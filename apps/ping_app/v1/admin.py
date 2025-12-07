from django.contrib import admin

from .models import PingLog, SystemHealth


@admin.register(PingLog)
class PingLogAdmin(admin.ModelAdmin):
    list_display = (
        "endpoint",
        "method",
        "status_code",
        "response_time_ms",
        "success",
        "created_at",
    )
    search_fields = ("endpoint", "error_message")
    list_filter = ("method", "status_code", "success", "created_at")
    readonly_fields = ("created_at",)


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = (
        "service_name",
        "service_type",
        "is_healthy",
        "response_time_ms",
        "checked_at",
    )
    search_fields = ("service_name", "error_message")
    list_filter = ("service_type", "is_healthy", "checked_at")
    readonly_fields = ("checked_at",)
