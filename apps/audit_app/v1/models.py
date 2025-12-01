# audit_app/models.py
import uuid

from django.db import models

from common.models import BaseModel


class AuditLog(BaseModel):
    """
    Comprehensive Audit Log model to track all system, security, and
    business events, ensuring accountability, compliance, and distributed tracing.
    """

    # --- TRACING & CORRELATION FIELDS ---
    trace_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="A UUID used for distributed tracing across services (e.g., OpenTelemetry span/trace ID).",
        editable=False,  # Should be set on creation, not edited later
        null=True,
        blank=True,
    )
    correlation_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="A generic identifier (e.g., request ID) linking related log entries, often across different parts of a single transaction.",
    )

    # --- ACTOR & ACTION FIELDS ---
    actor_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="ID of the user who performed the action"
    )
    actor_email = models.CharField(
        max_length=255, null=True, blank=True, help_text="Email of the user who performed the action"
    )
    action = models.CharField(
        max_length=50,
        help_text=(
            "Action performed (e.g., CREATE, UPDATE, DELETE, " "LOGIN, PERMISSION_GRANT, STATE_CHANGE)"
        ),
    )

    # --- TARGET OBJECT FIELDS ---
    target_model = models.CharField(
        max_length=255, help_text="Model path of the modified object (e.g. 'apps.animals.Animal')"
    )
    target_object_id = models.CharField(max_length=255, help_text="ID of the modified object")
    object_representation = models.TextField(
        null=True,
        blank=True,
        help_text="A string representation of the modified object (e.g., its name or title)",
    )

    # --- CONTEXT & DATA FIELDS ---
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON diff of changes (standard format: {'field': {'old': 'val', 'new': 'val'}})",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the actor")
    user_agent = models.TextField(null=True, blank=True, help_text="User Agent string of the actor")
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text="The session key associated with the action, useful for forensic linking",
    )

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            # Original indexes for quick lookups
            models.Index(fields=["target_model", "target_object_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["actor_id"]),
            models.Index(fields=["actor_email"]),
            models.Index(fields=["created_at"]),
            # New index for tracing/correlation
            models.Index(fields=["correlation_id"]),
        ]
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log Entries"

    def __str__(self):
        actor = self.actor_email or self.actor_id or "System"
        obj_repr = self.object_representation or f"{self.target_model}({self.target_object_id})"
        return f"[{self.action}] on {obj_repr} by {actor}"
