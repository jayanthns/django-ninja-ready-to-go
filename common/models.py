import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps.
    """

    AUDIT_ENABLED = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, help_text="Creation timestamp")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update timestamp")

    class Meta:
        abstract = True
