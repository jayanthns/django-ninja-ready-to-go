from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "actor_email",
        "target_model",
        "target_object_id",
        "ip_address",
        "created_at",
    )
    search_fields = (
        "trace_id",
        "correlation_id",
        "actor_id",
        "actor_email",
        "target_object_id",
        "action",
    )
    list_filter = ("action", "target_model", "created_at")
    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
