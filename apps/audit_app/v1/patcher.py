from asgiref.sync import async_to_sync

from common.logger_helper import get_request_logger

from .context import get_normalized_context
from .task_dispatcher import TaskDispatcher
from .utils import compute_create_diff, compute_delete_diff, compute_update_diff


class AuditPatcher:
    """
    Centralized class encapsulating all async + sync auditing behaviors.
    DRY + SOLID compliant.
    """

    # ------------------------------------------------------------------
    # 🔥 Shared internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ctx():
        return get_normalized_context()

    # ------------------------------------------------------------------
    # 🔥 Instance serialization
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_instance(instance):
        return {
            "target_model": f"{instance._meta.app_label}.{instance._meta.model_name}",
            "target_object_id": str(instance.pk),
            "object_representation": str(instance),
        }

    # ---- Async audit dispatchers ----

    @classmethod
    async def audit_create_async(cls, instance, changes):
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.audit_create_async")
        ctx = cls._ctx()
        payload = {
            **ctx,
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        await TaskDispatcher.dispatch_create(payload=payload)
        if logger:
            logger.info("[2] Exiting AuditPatcher.audit_create_async")
        # await AuditService.log_create(instance=instance, changes=changes, **ctx)

    @classmethod
    async def audit_update_async(cls, instance, changes):
        if not changes:
            return
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.audit_update_async")
        ctx = cls._ctx()
        payload = {**ctx, **cls.serialize_instance(instance), "changes": changes}
        await TaskDispatcher.dispatch_update(payload=payload)
        if logger:
            logger.info("[2] Exiting AuditPatcher.audit_update_async")
        # await AuditService.log_update(instance=instance, changes=changes, **ctx)

    @classmethod
    async def audit_delete_async(cls, instance, changes):
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.audit_delete_async")
        ctx = cls._ctx()
        payload = {**ctx, **cls.serialize_instance(instance), "changes": changes}
        await TaskDispatcher.dispatch_delete(payload=payload)
        if logger:
            logger.info("[2] Exiting AuditPatcher.audit_delete_async")
        # await AuditService.log_delete(instance=instance, changes=changes, **ctx)

    # ---- Sync audit dispatchers ----

    @classmethod
    def audit_create_sync(cls, instance, changes):
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.audit_create_sync")
        ctx = cls._ctx()
        payload = {
            **ctx,
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        async_to_sync(TaskDispatcher.dispatch_create)(payload=payload)
        if logger:
            logger.info("[2] Exiting AuditPatcher.audit_create_sync")
        # AuditService.log_create_sync(instance=instance, changes=changes, **ctx)

    @classmethod
    def audit_update_sync(cls, instance, changes):
        if not changes:
            return
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.audit_update_sync")
        ctx = cls._ctx()
        payload = {**ctx, **cls.serialize_instance(instance), "changes": changes}
        async_to_sync(TaskDispatcher.dispatch_update)(payload=payload)
        if logger:
            logger.info("[2] Exiting AuditPatcher.audit_update_sync")

        # AuditService.log_update_sync(instance=instance, changes=changes, **ctx)

    @classmethod
    def audit_delete_sync(cls, instance, changes):
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.audit_delete_sync")
        ctx = cls._ctx()
        payload = {**ctx, **cls.serialize_instance(instance), "changes": changes}
        async_to_sync(TaskDispatcher.dispatch_delete)(payload=payload)
        if logger:
            logger.info("[2] Exiting AuditPatcher.audit_delete_sync")

        # AuditService.log_delete_sync(instance=instance, changes=changes, **ctx)

    # ------------------------------------------------------------------
    # 🔥 ASYNC MODEL INSTANCE PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    async def asave(self, *args, **kwargs):
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.asave")

        if getattr(self, "_audit_in_progress", False):
            if logger:
                logger.info("[2] Recursion detected in asave, skipping audit")
            return await self.__original_asave__(*args, **kwargs)

        self._audit_in_progress = True
        try:
            is_new = self.pk is None
            old = None

            if logger:
                logger.info("[2] Checking existing instance for asave")

            if not is_new:
                try:
                    old = await self.__class__.objects.aget(pk=self.pk)
                except self.__class__.DoesNotExist:
                    old = None

            if old is None:
                is_new = True

            result = await self.__original_asave__(*args, **kwargs)

            if not getattr(self, "AUDIT_ENABLED", False):
                if logger:
                    logger.info("[3] Audit disabled for model, exiting asave")
                return result

            if is_new:
                if logger:
                    logger.info("[3] Auditing creation in asave")
                changes = compute_create_diff(self)
                await AuditPatcher.audit_create_async(self, changes)
            else:
                if logger:
                    logger.info("[3] Auditing update in asave")
                changes = compute_update_diff(old, self)
                await AuditPatcher.audit_update_async(self, changes)

            if logger:
                logger.info("[4] Exiting AuditPatcher.asave")
            return result
        finally:
            self._audit_in_progress = False

    @staticmethod
    async def adelete(self, *args, **kwargs):
        """
        Async audited delete() for a single instance.
        """
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.adelete")

        changes = compute_delete_diff(self)

        result = await self.__original_adelete__(*args, **kwargs)

        if getattr(self, "AUDIT_ENABLED", False):
            if logger:
                logger.info("[2] Auditing deletion in adelete")
            await AuditPatcher.audit_delete_async(self, changes)

        if logger:
            logger.info("[3] Exiting AuditPatcher.adelete")
        return result

    # ------------------------------------------------------------------
    # 🔥 ASYNC MANAGER / QUERYSET PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    async def aupdate(self, **kwargs):
        model = self.model
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.aupdate")

        if not getattr(model, "AUDIT_ENABLED", False):
            return await self.__original_aupdate__(**kwargs)

        before = [obj async for obj in self._clone().all()]

        updated = await self.__original_aupdate__(**kwargs)
        if updated == 0:
            if logger:
                logger.info("[2] No records updated in aupdate")
            return updated

        after = [obj async for obj in self._clone().all()]

        for old_obj, new_obj in zip(before, after):
            if logger:
                logger.info(f"[3] Auditing update for object: {new_obj.pk}")
            diff = compute_update_diff(old_obj, new_obj)
            await AuditPatcher.audit_update_async(new_obj, diff)

        if logger:
            logger.info("[4] Exiting AuditPatcher.aupdate")
        return updated

    @staticmethod
    async def adelete_queryset(self, **kwargs):
        model = self.model
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.adelete_queryset")

        if not getattr(model, "AUDIT_ENABLED", False):
            return await self.__original_adelete__(**kwargs)

        before = [obj async for obj in self._clone().all()]

        deleted, details = await self.__original_adelete__(**kwargs)

        if deleted:
            if logger:
                logger.info("[2] Auditing queryset deletion")
            for inst in before:
                diff = compute_delete_diff(inst)
                await AuditPatcher.audit_delete_async(inst, diff)

        if logger:
            logger.info("[3] Exiting AuditPatcher.adelete_queryset")
        return deleted, details

    # ------------------------------------------------------------------
    # 🔥 SYNC VERSION OF PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    def save(self, *args, **kwargs):
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.save")

        if getattr(self, "_audit_in_progress", False):
            if logger:
                logger.info("[2] Recursion detected in save, skipping audit")
            return self.__original_save__(*args, **kwargs)

        self._audit_in_progress = True
        try:
            is_new = self.pk is None
            old = None

            if logger:
                logger.info("[2] Checking existing instance for save")

            if not is_new:
                try:
                    old = self.__class__.objects.get(pk=self.pk)
                except self.__class__.DoesNotExist:
                    old = None

            if old is None:
                is_new = True

            result = self.__original_save__(*args, **kwargs)

            if not getattr(self, "AUDIT_ENABLED", False):
                if logger:
                    logger.info("[3] Audit disabled for model, exiting save")
                return result

            if is_new:
                if logger:
                    logger.info("[3] Auditing creation in save")
                changes = compute_create_diff(self)
                AuditPatcher.audit_create_sync(self, changes)
            else:
                if logger:
                    logger.info("[3] Auditing update in save")
                changes = compute_update_diff(old, self)
                AuditPatcher.audit_update_sync(self, changes)

            if logger:
                logger.info("[4] Exiting AuditPatcher.save")
            return result
        finally:
            self._audit_in_progress = False

    @staticmethod
    def delete(self, *args, **kwargs):
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.delete")
        changes = compute_delete_diff(self)

        result = self.__original_delete__(*args, **kwargs)

        if getattr(self, "AUDIT_ENABLED", False):
            if logger:
                logger.info("[2] Auditing deletion in delete")
            AuditPatcher.audit_delete_sync(self, changes)

        if logger:
            logger.info("[3] Exiting AuditPatcher.delete")
        return result

    @staticmethod
    def update(self, **kwargs):
        model = self.model
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.update")

        if not getattr(model, "AUDIT_ENABLED", False):
            return self.__original_update__(**kwargs)

        before = list(self._clone().all())

        updated = self.__original_update__(**kwargs)
        if updated == 0:
            if logger:
                logger.info("[2] No records updated in update")
            return updated

        after = list(self._clone().all())

        for old_obj, new_obj in zip(before, after):
            if logger:
                logger.info(f"[3] Auditing update for object: {new_obj.pk}")
            diff = compute_update_diff(old_obj, new_obj)
            AuditPatcher.audit_update_sync(new_obj, diff)

        if logger:
            logger.info("[4] Exiting AuditPatcher.update")
        return updated

    @staticmethod
    def delete_queryset(self, **kwargs):
        model = self.model
        logger = get_request_logger()
        if logger:
            logger.info("[1] Entering AuditPatcher.delete_queryset")

        # Skip if auditing disabled
        if not getattr(model, "AUDIT_ENABLED", False):
            return self.__original_delete__(**kwargs)

        # Before snapshot
        before = list(self._clone().all())

        # Execute actual delete() on queryset
        deleted, details = self.__original_delete__(**kwargs)

        # Emit audit logs
        if deleted:
            if logger:
                logger.info("[2] Auditing queryset deletion")
            for inst in before:
                diff = compute_delete_diff(inst)
                AuditPatcher.audit_delete_sync(inst, diff)

        if logger:
            logger.info("[3] Exiting AuditPatcher.delete_queryset")
        return deleted, details
