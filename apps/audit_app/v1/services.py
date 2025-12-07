from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.db.models import Model

from common.enums import AuditAction
from common.utils import normalize_value

from .models import AuditLog

User = get_user_model()


class AuditService:
    """
    Service for creating audit logs.
    Ensures all audit-mode fields are fully captured.
    """

    @staticmethod
    async def log_event(
        action: str,
        target_model: str,
        target_object_id: str,
        trace_id: str,
        changes: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_key: Optional[str] = None,
        object_representation: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Lowest-level unified audit log writer.
        Normalizes all values to ensure JSON safety.
        """

        # --------------------------
        # Normalize CHANGE DICT
        # --------------------------
        normalized_changes: Dict[str, Dict[str, Any]] = {}

        if changes:
            for field, diff in changes.items():
                normalized_changes[field] = {
                    "old": normalize_value(diff.get("old")),
                    "new": normalize_value(diff.get("new")),
                }

        # --------------------------
        # Normalize top-level fields
        # --------------------------
        normalized_payload = {
            "action": normalize_value(action),
            "target_model": normalize_value(target_model),
            "target_object_id": normalize_value(target_object_id),
            "trace_id": normalize_value(trace_id),
            "changes": normalized_changes,
            "actor_id": normalize_value(actor_id),
            "actor_email": normalize_value(actor_email),
            "correlation_id": normalize_value(correlation_id),
            "session_key": normalize_value(session_key),
            "object_representation": normalize_value(object_representation),
            "ip_address": normalize_value(ip_address),
            "user_agent": normalize_value(user_agent),
        }

        return await AuditLog.objects.acreate(**normalized_payload)

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------

    @classmethod
    async def log_create(
        cls,
        instance: Model,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        trace_id: str = "",
        correlation_id: Optional[str] = None,
        session_key: Optional[str] = None,
        object_representation: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:

        return await cls.log_event(
            action=AuditAction.CREATE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            trace_id=trace_id,
            changes=changes,
            actor_id=actor_id,
            actor_email=actor_email,
            correlation_id=correlation_id,
            session_key=session_key,
            object_representation=object_representation,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------

    @classmethod
    async def log_update(
        cls,
        instance: Model,
        changes: Dict[str, Any],
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        trace_id: str = "",
        correlation_id: Optional[str] = None,
        session_key: Optional[str] = None,
        object_representation: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:

        return await cls.log_event(
            action=AuditAction.UPDATE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            trace_id=trace_id,
            changes=changes,
            actor_id=actor_id,
            actor_email=actor_email,
            correlation_id=correlation_id,
            session_key=session_key,
            object_representation=object_representation,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------

    @classmethod
    async def log_delete(
        cls,
        instance: Model,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        trace_id: str = "",
        correlation_id: Optional[str] = None,
        session_key: Optional[str] = None,
        object_representation: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:

        return await cls.log_event(
            action=AuditAction.DELETE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            trace_id=trace_id,
            changes={},
            actor_id=actor_id,
            actor_email=actor_email,
            correlation_id=correlation_id,
            session_key=session_key,
            object_representation=object_representation,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # -------------------------------------------------------------------------
    # SYNC METHODS (For Django Admin, Shell, etc.)
    # -------------------------------------------------------------------------

    @staticmethod
    def log_event_sync(
        action: str,
        target_model: str,
        target_object_id: str,
        trace_id: str,
        changes: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_key: Optional[str] = None,
        object_representation: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Synchronous version of log_event.
        """

        # --------------------------
        # Normalize CHANGE DICT
        # --------------------------
        normalized_changes: Dict[str, Dict[str, Any]] = {}

        if changes:
            for field, diff in changes.items():
                normalized_changes[field] = {
                    "old": normalize_value(diff.get("old")),
                    "new": normalize_value(diff.get("new")),
                }

        # --------------------------
        # Normalize top-level fields
        # --------------------------
        normalized_payload = {
            "action": normalize_value(action),
            "target_model": normalize_value(target_model),
            "target_object_id": normalize_value(target_object_id),
            "trace_id": normalize_value(trace_id),
            "changes": normalized_changes,
            "actor_id": normalize_value(actor_id),
            "actor_email": normalize_value(actor_email),
            "correlation_id": normalize_value(correlation_id),
            "session_key": normalize_value(session_key),
            "object_representation": normalize_value(object_representation),
            "ip_address": normalize_value(ip_address),
            "user_agent": normalize_value(user_agent),
        }

        return AuditLog.objects.create(**normalized_payload)

    @classmethod
    def log_create_sync(
        cls,
        instance: Model,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        trace_id: str = "",
        correlation_id: Optional[str] = None,
        session_key: Optional[str] = None,
        object_representation: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return cls.log_event_sync(
            action=AuditAction.CREATE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            trace_id=trace_id,
            changes=changes,
            actor_id=actor_id,
            actor_email=actor_email,
            correlation_id=correlation_id,
            session_key=session_key,
            object_representation=object_representation,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def log_update_sync(
        cls,
        instance: Model,
        changes: Dict[str, Any],
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        trace_id: str = "",
        correlation_id: Optional[str] = None,
        session_key: Optional[str] = None,
        object_representation: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return cls.log_event_sync(
            action=AuditAction.UPDATE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            trace_id=trace_id,
            changes=changes,
            actor_id=actor_id,
            actor_email=actor_email,
            correlation_id=correlation_id,
            session_key=session_key,
            object_representation=object_representation,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def log_delete_sync(
        cls,
        instance: Model,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        trace_id: str = "",
        correlation_id: Optional[str] = None,
        session_key: Optional[str] = None,
        object_representation: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        return cls.log_event_sync(
            action=AuditAction.DELETE,
            target_model=f"{instance._meta.app_label}.{instance._meta.model_name}",
            target_object_id=str(instance.pk),
            trace_id=trace_id,
            changes={},
            actor_id=actor_id,
            actor_email=actor_email,
            correlation_id=correlation_id,
            session_key=session_key,
            object_representation=object_representation,
            ip_address=ip_address,
            user_agent=user_agent,
        )
