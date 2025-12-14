from asgiref.sync import async_to_sync

from common.logger_helper import get_request_logger

from .context import get_normalized_context
from .task_dispatcher import TaskDispatcher
from .utils import compute_create_diff, compute_delete_diff, compute_update_diff


class AuditPatcher:
    """
    Centralized class encapsulating all async + sync auditing behaviors.

    RULES:
    - Instance save / asave is the ONLY source of update audits
    - QuerySet update / aupdate is FORBIDDEN for audited models
    """

    # ------------------------------------------------------------------
    # 🔥 Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ctx():
        return get_normalized_context()

    @staticmethod
    def serialize_instance(instance):
        return {
            "target_model": f"{instance._meta.app_label}.{instance._meta.model_name}",
            "target_object_id": str(instance.pk),
            "object_representation": str(instance),
        }

    # ------------------------------------------------------------------
    # 🔥 ASYNC AUDIT DISPATCHERS
    # ------------------------------------------------------------------

    @classmethod
    async def audit_create_async(cls, instance, changes):
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.audit_create_async")

        payload = {
            **cls._ctx(),
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        await TaskDispatcher.dispatch_create(payload=payload)

        logger.info("[2] Exiting AuditPatcher.audit_create_async")

    @classmethod
    async def audit_update_async(cls, instance, changes):
        if not changes:
            return

        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.audit_update_async")

        payload = {
            **cls._ctx(),
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        await TaskDispatcher.dispatch_update(payload=payload)

        logger.info("[2] Exiting AuditPatcher.audit_update_async")

    @classmethod
    async def audit_delete_async(cls, instance, changes):
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.audit_delete_async")

        payload = {
            **cls._ctx(),
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        await TaskDispatcher.dispatch_delete(payload=payload)

        logger.info("[2] Exiting AuditPatcher.audit_delete_async")

    # ------------------------------------------------------------------
    # 🔥 SYNC AUDIT DISPATCHERS
    # ------------------------------------------------------------------

    @classmethod
    def audit_create_sync(cls, instance, changes):
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.audit_create_sync")

        payload = {
            **cls._ctx(),
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        async_to_sync(TaskDispatcher.dispatch_create)(payload=payload)

        logger.info("[2] Exiting AuditPatcher.audit_create_sync")

    @classmethod
    def audit_update_sync(cls, instance, changes):
        if not changes:
            return

        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.audit_update_sync")

        payload = {
            **cls._ctx(),
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        async_to_sync(TaskDispatcher.dispatch_update)(payload=payload)

        logger.info("[2] Exiting AuditPatcher.audit_update_sync")

    @classmethod
    def audit_delete_sync(cls, instance, changes):
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.audit_delete_sync")

        payload = {
            **cls._ctx(),
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        async_to_sync(TaskDispatcher.dispatch_delete)(payload=payload)

        logger.info("[2] Exiting AuditPatcher.audit_delete_sync")

    # ------------------------------------------------------------------
    # 🔥 ASYNC INSTANCE PATCHES (SOURCE OF TRUTH)
    # ------------------------------------------------------------------

    @staticmethod
    async def asave(self, *args, **kwargs):
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.asave")

        if getattr(self, "_audit_in_progress", False):
            logger.info("[2] Recursion detected in asave, skipping audit")
            return await self.__original_asave__(*args, **kwargs)

        self._audit_in_progress = True
        try:
            is_new = self.pk is None
            old = None

            if not is_new:
                try:
                    old = await self.__class__.objects.aget(pk=self.pk)
                except self.__class__.DoesNotExist:
                    old = None

            if old is None:
                is_new = True

            result = await self.__original_asave__(*args, **kwargs)

            if not getattr(self, "AUDIT_ENABLED", False):
                logger.info("[3] Audit disabled for model, exiting asave")
                return result

            if is_new:
                logger.info("[3] Auditing creation in asave")
                changes = compute_create_diff(self)
                await AuditPatcher.audit_create_async(self, changes)
            else:
                logger.info("[3] Auditing update in asave")
                changes = compute_update_diff(old, self)
                await AuditPatcher.audit_update_async(self, changes)

            logger.info("[4] Exiting AuditPatcher.asave")
            return result
        finally:
            self._audit_in_progress = False

    @staticmethod
    async def adelete(self, *args, **kwargs):
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.adelete")

        changes = compute_delete_diff(self)
        result = await self.__original_adelete__(*args, **kwargs)

        if getattr(self, "AUDIT_ENABLED", False):
            logger.info("[2] Auditing deletion in adelete")
            await AuditPatcher.audit_delete_async(self, changes)

        logger.info("[3] Exiting AuditPatcher.adelete")
        return result

    # ------------------------------------------------------------------
    # 🔥 ASYNC QUERYSET PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    async def aupdate(self, **kwargs):
        model = self.model
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.aupdate")

        if getattr(model, "AUDIT_ENABLED", False):
            logger.error(
                "[2] AUDIT VIOLATION: Forbidden QuerySet.aupdate",
                extra={"model": model.__name__, "kwargs": kwargs},
            )
            raise RuntimeError(
                f"[AUDIT VIOLATION] QuerySet.aupdate() is forbidden for audited model "
                f"{model.__name__}. Use instance.asave()."
            )

        result = await self.__original_aupdate__(**kwargs)
        logger.info("[3] Exiting AuditPatcher.aupdate")
        return result

    @staticmethod
    async def adelete_queryset(self, **kwargs):
        model = self.model
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.adelete_queryset")

        if not getattr(model, "AUDIT_ENABLED", False):
            result = await self.__original_adelete__(**kwargs)
            logger.info("[2] Exiting AuditPatcher.adelete_queryset")
            return result

        before = [obj async for obj in self._clone().all()]
        deleted, details = await self.__original_adelete__(**kwargs)

        if deleted:
            logger.info("[2] Auditing queryset deletion")
            for inst in before:
                diff = compute_delete_diff(inst)
                await AuditPatcher.audit_delete_async(inst, diff)

        logger.info("[3] Exiting AuditPatcher.adelete_queryset")
        return deleted, details

    # ------------------------------------------------------------------
    # 🔥 SYNC INSTANCE PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    def save(self, *args, **kwargs):
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.save")

        if getattr(self, "_audit_in_progress", False):
            logger.info("[2] Recursion detected in save, skipping audit")
            return self.__original_save__(*args, **kwargs)

        self._audit_in_progress = True
        try:
            is_new = self.pk is None
            old = None

            if not is_new:
                try:
                    old = self.__class__.objects.get(pk=self.pk)
                except self.__class__.DoesNotExist:
                    old = None

            if old is None:
                is_new = True

            result = self.__original_save__(*args, **kwargs)

            if not getattr(self, "AUDIT_ENABLED", False):
                logger.info("[3] Audit disabled for model, exiting save")
                return result

            if is_new:
                logger.info("[3] Auditing creation in save")
                changes = compute_create_diff(self)
                AuditPatcher.audit_create_sync(self, changes)
            else:
                logger.info("[3] Auditing update in save")
                changes = compute_update_diff(old, self)
                AuditPatcher.audit_update_sync(self, changes)

            logger.info("[4] Exiting AuditPatcher.save")
            return result
        finally:
            self._audit_in_progress = False

    @staticmethod
    def delete(self, *args, **kwargs):
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.delete")

        changes = compute_delete_diff(self)
        result = self.__original_delete__(*args, **kwargs)

        if getattr(self, "AUDIT_ENABLED", False):
            logger.info("[2] Auditing deletion in delete")
            AuditPatcher.audit_delete_sync(self, changes)

        logger.info("[3] Exiting AuditPatcher.delete")
        return result

    # ------------------------------------------------------------------
    # 🔥 SYNC QUERYSET PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    def update(self, **kwargs):
        model = self.model
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.update")

        if getattr(model, "AUDIT_ENABLED", False):
            logger.error(
                "[2] AUDIT VIOLATION: Forbidden QuerySet.update",
                extra={"model": model.__name__, "kwargs": kwargs},
            )
            raise RuntimeError(
                f"[AUDIT VIOLATION] QuerySet.update() is forbidden for audited model "
                f"{model.__name__}. Use instance.save()."
            )

        result = self.__original_update__(**kwargs)
        logger.info("[3] Exiting AuditPatcher.update")
        return result

    @staticmethod
    def delete_queryset(self, **kwargs):
        model = self.model
        logger = get_request_logger()
        logger.info("[1] Entering AuditPatcher.delete_queryset")

        if not getattr(model, "AUDIT_ENABLED", False):
            result = self.__original_delete__(**kwargs)
            logger.info("[2] Exiting AuditPatcher.delete_queryset")
            return result

        before = list(self._clone().all())
        deleted, details = self.__original_delete__(**kwargs)

        if deleted:
            logger.info("[2] Auditing queryset deletion")
            for inst in before:
                diff = compute_delete_diff(inst)
                AuditPatcher.audit_delete_sync(inst, diff)

        logger.info("[3] Exiting AuditPatcher.delete_queryset")
        return deleted, details
