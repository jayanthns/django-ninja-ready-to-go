from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditAction(models.TextChoices):
    CREATE = "CREATE", _("Create")
    UPDATE = "UPDATE", _("Update")
    DELETE = "DELETE", _("Delete")
    LOGIN = "LOGIN", _("Login")
    LOGOUT = "LOGOUT", _("Logout")
    OTHER = "OTHER", _("Other")
    # Add more actions as needed
