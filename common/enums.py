from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditAction(models.TextChoices):
    # CRUD Operations
    CREATE = "CREATE", _("Create")
    UPDATE = "UPDATE", _("Update")
    DELETE = "DELETE", _("Delete")

    # Authentication
    LOGIN = "LOGIN", _("Login")
    LOGOUT = "LOGOUT", _("Logout")
    LOGIN_FAILED = "LOGIN_FAILED", _("Login Failed")
    LOGOUT_FAILED = "LOGOUT_FAILED", _("Logout Failed")

    # Security & Account
    PASSWORD_CHANGE = "PASSWORD_CHANGE", _("Password Change")
    PASSWORD_CHANGE_FAILED = "PASSWORD_CHANGE_FAILED", _("Password Change Failed")
    ACCOUNT_LOCK = "ACCOUNT_LOCK", _("Account Lock")
    ACCOUNT_UNLOCK = "ACCOUNT_UNLOCK", _("Account Unlock")

    # Permissions
    PERMISSION_GRANT = "PERMISSION_GRANT", _("Permission Grant")
    PERMISSION_REVOKE = "PERMISSION_REVOKE", _("Permission Revoke")

    # Data Operations
    IMPORT = "IMPORT", _("Import")
    EXPORT = "EXPORT", _("Export")
    BULK_DELETE = "BULK_DELETE", _("Bulk Delete")
    BULK_UPDATE = "BULK_UPDATE", _("Bulk Update")
    MIGRATION_RUN = "MIGRATION_RUN", _("Migration Run")
    DOWNLOAD = "DOWNLOAD", _("Download")

    # Workflow & State
    STATE_CHANGE = "STATE_CHANGE", _("State Change")
    APPROVAL = "APPROVAL", _("Approval")
    REVERT = "REVERT", _("Revert")
    COMMENT = "COMMENT", _("Comment")

    # General
    SETTINGS_UPDATE = "SETTINGS_UPDATE", _("Settings Update")
    OTHER = "OTHER", _("Other")
    # Add more actions as needed
