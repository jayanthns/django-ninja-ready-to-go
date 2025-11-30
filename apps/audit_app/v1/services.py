from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.db.models import Model

from common.enums import AuditAction

from .models import AuditLog

User = get_user_model()


class AuditService:
    """
    Service for creating audit logs.
    Designed to be injected into other services.
    """

    @staticmethod
    async def log_event(
        action: str,
        target_model: str,
        target_object_id: str,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Generic method to log an event.
        Accepts actor_id and actor_email directly.
        """
        return await AuditLog.objects.acreate(
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            target_model=target_model,
            target_object_id=target_object_id,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    async def log_create(
        cls,
        instance: Model,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditLog:
        """
        Log a creation event.
        """
        return await cls.log_event(
            action=AuditAction.CREATE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            actor_id=actor_id,
            actor_email=actor_email,
            changes=changes,
            **kwargs,
        )

    @classmethod
    async def log_update(
        cls,
        instance: Model,
        changes: Dict[str, Any],
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        **kwargs,
    ) -> AuditLog:
        """
        Log an update event.
        """
        return await cls.log_event(
            action=AuditAction.UPDATE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            actor_id=actor_id,
            actor_email=actor_email,
            changes=changes,
            **kwargs,
        )

    @classmethod
    async def log_delete(
        cls, instance: Model, actor_id: Optional[str] = None, actor_email: Optional[str] = None, **kwargs
    ) -> AuditLog:
        """
        Log a deletion event.
        """
        return await cls.log_event(
            action=AuditAction.DELETE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            actor_id=actor_id,
            actor_email=actor_email,
            **kwargs,
        )
