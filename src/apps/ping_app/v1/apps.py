from django.apps import AppConfig


class PingAppV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ping_app.v1"
    verbose_name = "Ping App V1"
