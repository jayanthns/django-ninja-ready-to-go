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
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        object_representation: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_key: Optional[str] = None,
    ) -> AuditLog:
        """
        Generic method to log an event.
        Accepts actor_id and actor_email directly.
        """
        return await AuditLog.objects.acreate(
            action=action,
            target_model=target_model,
            target_object_id=target_object_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            actor_id=actor_id,
            actor_email=actor_email,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key,
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
            trace_id=kwargs.get("trace_id"),
            correlation_id=kwargs.get("correlation_id"),
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
            trace_id=kwargs.get("trace_id"),
            correlation_id=kwargs.get("correlation_id"),
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
