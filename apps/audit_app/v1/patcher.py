from asgiref.sync import async_to_sync

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
        ctx = cls._ctx()
        payload = {
            **ctx,
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        await TaskDispatcher.dispatch_create(payload=payload)
        # await AuditService.log_create(instance=instance, changes=changes, **ctx)

    @classmethod
    async def audit_update_async(cls, instance, changes):
        if not changes:
            return
        ctx = cls._ctx()
        payload = {**ctx, **cls.serialize_instance(instance), "changes": changes}
        await TaskDispatcher.dispatch_update(payload=payload)
        # await AuditService.log_update(instance=instance, changes=changes, **ctx)

    @classmethod
    async def audit_delete_async(cls, instance, changes):
        ctx = cls._ctx()
        payload = {**ctx, **cls.serialize_instance(instance), "changes": changes}
        await TaskDispatcher.dispatch_delete(payload=payload)
        # await AuditService.log_delete(instance=instance, changes=changes, **ctx)

    # ---- Sync audit dispatchers ----

    @classmethod
    def audit_create_sync(cls, instance, changes):
        ctx = cls._ctx()
        payload = {
            **ctx,
            **cls.serialize_instance(instance),
            "changes": changes,
        }
        async_to_sync(TaskDispatcher.dispatch_create)(payload=payload)
        # AuditService.log_create_sync(instance=instance, changes=changes, **ctx)

    @classmethod
    def audit_update_sync(cls, instance, changes):
        if not changes:
            return
        ctx = cls._ctx()
        payload = {**ctx, **cls.serialize_instance(instance), "changes": changes}
        async_to_sync(TaskDispatcher.dispatch_update)(payload=payload)

        # AuditService.log_update_sync(instance=instance, changes=changes, **ctx)

    @classmethod
    def audit_delete_sync(cls, instance, changes):
        ctx = cls._ctx()
        payload = {**ctx, **cls.serialize_instance(instance), "changes": changes}
        async_to_sync(TaskDispatcher.dispatch_delete)(payload=payload)

        # AuditService.log_delete_sync(instance=instance, changes=changes, **ctx)

    # ------------------------------------------------------------------
    # 🔥 ASYNC MODEL INSTANCE PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    async def asave(self, *args, **kwargs):
        if getattr(self, "_audit_in_progress", False):
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
                return result

            if is_new:
                changes = compute_create_diff(self)
                await AuditPatcher.audit_create_async(self, changes)
            else:
                changes = compute_update_diff(old, self)
                await AuditPatcher.audit_update_async(self, changes)

            return result
        finally:
            self._audit_in_progress = False

    @staticmethod
    async def adelete(self, *args, **kwargs):
        """
        Async audited delete() for a single instance.
        """
        changes = compute_delete_diff(self)

        result = await self.__original_adelete__(*args, **kwargs)

        if getattr(self, "AUDIT_ENABLED", False):
            await AuditPatcher.audit_delete_async(self, changes)

        return result

    # ------------------------------------------------------------------
    # 🔥 ASYNC MANAGER / QUERYSET PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    async def aupdate(self, **kwargs):
        model = self.model

        if not getattr(model, "AUDIT_ENABLED", False):
            return await self.__original_aupdate__(**kwargs)

        before = [obj async for obj in self._clone().all()]

        updated = await self.__original_aupdate__(**kwargs)
        if updated == 0:
            return updated

        after = [obj async for obj in self._clone().all()]

        for old_obj, new_obj in zip(before, after):
            diff = compute_update_diff(old_obj, new_obj)
            await AuditPatcher.audit_update_async(new_obj, diff)

        return updated

    @staticmethod
    async def adelete_queryset(self, **kwargs):
        model = self.model

        if not getattr(model, "AUDIT_ENABLED", False):
            return await self.__original_adelete_queryset__(**kwargs)

        before = [obj async for obj in self._clone().all()]

        deleted, details = await self.__original_adelete_queryset__(**kwargs)

        if deleted:
            for inst in before:
                diff = compute_delete_diff(inst)
                await AuditPatcher.audit_delete_async(inst, diff)

        return deleted, details

    # ------------------------------------------------------------------
    # 🔥 SYNC VERSION OF PATCHES
    # ------------------------------------------------------------------

    @staticmethod
    def save(self, *args, **kwargs):
        if getattr(self, "_audit_in_progress", False):
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
                return result

            if is_new:
                changes = compute_create_diff(self)
                AuditPatcher.audit_create_sync(self, changes)
            else:
                changes = compute_update_diff(old, self)
                AuditPatcher.audit_update_sync(self, changes)

            return result
        finally:
            self._audit_in_progress = False

    @staticmethod
    def delete(self, *args, **kwargs):
        changes = compute_delete_diff(self)

        result = self.__original_delete__(*args, **kwargs)

        if getattr(self, "AUDIT_ENABLED", False):
            AuditPatcher.audit_delete_sync(self, changes)

        return result

    @staticmethod
    def update(self, **kwargs):
        model = self.model

        if not getattr(model, "AUDIT_ENABLED", False):
            return self.__original_update__(**kwargs)

        before = list(self._clone().all())

        updated = self.__original_update__(**kwargs)
        if updated == 0:
            return updated

        after = list(self._clone().all())

        for old_obj, new_obj in zip(before, after):
            diff = compute_update_diff(old_obj, new_obj)
            AuditPatcher.audit_update_sync(new_obj, diff)

        return updated

    @staticmethod
    def delete_queryset(self, **kwargs):
        model = self.model

        # Skip if auditing disabled
        if not getattr(model, "AUDIT_ENABLED", False):
            return self.__original_delete__(**kwargs)

        # Before snapshot
        before = list(self._clone().all())

        # Execute actual delete() on queryset
        deleted, details = self.__original_delete__(**kwargs)

        # Emit audit logs
        if deleted:
            for inst in before:
                diff = compute_delete_diff(inst)
                AuditPatcher.audit_delete_sync(inst, diff)

        return deleted, details
