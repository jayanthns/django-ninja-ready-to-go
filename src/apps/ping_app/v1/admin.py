from django.contrib import admin

from .models import PingLog, SystemHealth


@admin.register(PingLog)
class PingLogAdmin(admin.ModelAdmin):
    """Admin interface for PingLog model."""

    list_display = ["endpoint", "method", "status_code", "response_time_ms", "success", "created_at"]
    list_filter = ["method", "status_code", "success", "created_at"]
    search_fields = ["endpoint", "error_message"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Request Details", {"fields": ("endpoint", "method", "request_headers")}),
        ("Response Details", {"fields": ("status_code", "response_time_ms", "success", "response_headers")}),
        ("Error Information", {"fields": ("error_message",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    """Admin interface for SystemHealth model."""

    list_display = ["service_name", "service_type", "is_healthy", "response_time_ms", "checked_at"]
    list_filter = ["service_type", "is_healthy", "checked_at"]
    search_fields = ["service_name", "error_message"]
    readonly_fields = ["checked_at"]
    ordering = ["-checked_at"]

    fieldsets = (
        ("Service Information", {"fields": ("service_name", "service_type")}),
        ("Health Status", {"fields": ("is_healthy", "response_time_ms")}),
        ("Error Information", {"fields": ("error_message",), "classes": ("collapse",)}),
        ("Additional Data", {"fields": ("metadata",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("checked_at",), "classes": ("collapse",)}),
    )
