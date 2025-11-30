from django.apps import AppConfig


class AuditAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit_app.v1"
    label = "apps_audit_app_v1"
