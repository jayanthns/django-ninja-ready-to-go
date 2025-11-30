from django.db import models

from common.models import BaseModel


class AuditLog(BaseModel):
    """
    Generic Audit Log model to track system events.
    """

    actor_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="ID of the user who performed the action"
    )
    actor_email = models.CharField(
        max_length=255, null=True, blank=True, help_text="Email of the user who performed the action"
    )
    action = models.CharField(max_length=50, help_text="Action performed (e.g., CREATE, UPDATE, DELETE)")
    target_model = models.CharField(
        max_length=255, help_text="Model path of the modified object (e.g. 'apps.animals.Animal')"
    )
    target_object_id = models.CharField(max_length=255, help_text="ID of the modified object")
    changes = models.JSONField(default=dict, blank=True, help_text="JSON diff of changes (before/after)")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the actor")
    user_agent = models.TextField(null=True, blank=True, help_text="User Agent string of the actor")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target_model", "target_object_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["actor_id"]),
            models.Index(fields=["actor_email"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        actor = self.actor_email or self.actor_id or "System"
        return f"{self.action} - {self.target_model} ({self.target_object_id}) by {actor}"
