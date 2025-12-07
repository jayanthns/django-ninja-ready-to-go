from .context import get_normalized_context
from .services import AuditService


async def audited_asave(self, *args, **kwargs):
    is_new = self.pk is None

    # BEFORE state
    old = None
    if not is_new:
        try:
            old = await self.__class__.objects.aget(pk=self.pk)
        except self.__class__.DoesNotExist:
            old = None

    if old is None:
        is_new = True

    # Perform actual save
    result = await self.__original_asave__(*args, **kwargs)

    # Skip if AUDIT_ENABLED=False
    if not getattr(self, "AUDIT_ENABLED", False):
        return result

    ctx = get_normalized_context()

    if is_new:
        # CREATE diff
        changes = {f.name: {"old": None, "new": getattr(self, f.name)} for f in self._meta.fields}

        await AuditService.log_create(
            instance=self,
            changes=changes,
            actor_id=ctx["actor_id"],
            actor_email=ctx["actor_email"],
            trace_id=ctx["trace_id"],
            correlation_id=ctx["correlation_id"],
            session_key=ctx["session_key"],
            object_representation=str(self),
            ip_address=ctx["ip_address"],
            user_agent=ctx["user_agent"],
        )

    else:
        # UPDATE diff
        diff = {}
        if old:
            for f in self._meta.fields:
                name = f.name
                old_val = getattr(old, name)
                new_val = getattr(self, name)
                if old_val != new_val:
                    diff[name] = {"old": old_val, "new": new_val}

            await AuditService.log_update(
                instance=self,
                changes=diff,
                actor_id=ctx["actor_id"],
                actor_email=ctx["actor_email"],
                trace_id=ctx["trace_id"],
                correlation_id=ctx["correlation_id"],
                session_key=ctx["session_key"],
                object_representation=str(self),
                ip_address=ctx["ip_address"],
                user_agent=ctx["user_agent"],
            )

    return result


async def audited_adelete(self, *args, **kwargs):
    result = await self.__original_adelete__(*args, **kwargs)

    if not getattr(self, "AUDIT_ENABLED", False):
        return result

    ctx = get_normalized_context()

    await AuditService.log_delete(
        instance=self,
        actor_id=ctx["actor_id"],
        actor_email=ctx["actor_email"],
        trace_id=ctx["trace_id"],
        correlation_id=ctx["correlation_id"],
        session_key=ctx["session_key"],
        object_representation=str(self),
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )

    return result


async def audited_acreate(self, **kwargs):
    instance = await self.__original_acreate__(**kwargs)

    model = self.model
    if not getattr(model, "AUDIT_ENABLED", False):
        return instance

    ctx = get_normalized_context()

    changes = {f.name: {"old": None, "new": getattr(instance, f.name)} for f in model._meta.fields}

    await AuditService.log_create(
        instance=instance,
        changes=changes,
        actor_id=ctx["actor_id"],
        actor_email=ctx["actor_email"],
        trace_id=ctx["trace_id"],
        correlation_id=ctx["correlation_id"],
        session_key=ctx["session_key"],
        object_representation=str(instance),
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )

    return instance


async def audited_aupdate(self, **kwargs):
    model = self.model

    # skip if auditing disabled
    if not getattr(model, "AUDIT_ENABLED", False):
        return await self.__original_aupdate__(**kwargs)

    # before snapshot
    before = [obj async for obj in self._clone().all()]

    # actual update
    updated_count = await self.__original_aupdate__(**kwargs)

    if updated_count == 0:
        return updated_count

    # after snapshot
    after = [obj async for obj in self._clone().all()]

    ctx = get_normalized_context()

    for old_obj, new_obj in zip(before, after):
        diff = {}
        for f in model._meta.fields:
            name = f.name
            old_val = getattr(old_obj, name)
            new_val = getattr(new_obj, name)
            if old_val != new_val:
                diff[name] = {"old": old_val, "new": new_val}

        await AuditService.log_update(
            instance=new_obj,
            changes=diff,
            actor_id=ctx["actor_id"],
            actor_email=ctx["actor_email"],
            trace_id=ctx["trace_id"],
            correlation_id=ctx["correlation_id"],
            session_key=ctx["session_key"],
            object_representation=str(new_obj),
            ip_address=ctx["ip_address"],
            user_agent=ctx["user_agent"],
        )

    return updated_count


async def audited_adelete_queryset(self, **kwargs):
    model = self.model

    # Skip non-audited models
    if not getattr(model, "AUDIT_ENABLED", False):
        return await self.__original_adelete_queryset__(**kwargs)

    # BEFORE SNAPSHOT
    # Must get instances BEFORE delete
    before_instances = [obj async for obj in self._clone().all()]

    # ACTUAL DELETE
    deleted_count, details = await self.__original_adelete_queryset__(**kwargs)

    if deleted_count == 0:
        return deleted_count, details

    ctx = get_normalized_context()

    # CREATE DELETE AUDIT ENTRY FOR EACH ROW
    for inst in before_instances:
        await AuditService.log_delete(
            instance=inst,
            actor_id=ctx["actor_id"],
            actor_email=ctx["actor_email"],
            trace_id=ctx["trace_id"],
            correlation_id=ctx["correlation_id"],
            session_key=ctx["session_key"],
            object_representation=str(inst),
            ip_address=ctx["ip_address"],
            user_agent=ctx["user_agent"],
        )

    return deleted_count, details


def audited_save(self, *args, **kwargs):
    is_new = self.pk is None

    # BEFORE state
    old = None
    if not is_new:
        try:
            old = self.__class__.objects.get(pk=self.pk)
        except self.__class__.DoesNotExist:
            old = None

    # Correction for UUIDs: if we couldn't find it, it's new
    if old is None:
        is_new = True

    # Perform actual save
    result = self.__original_save__(*args, **kwargs)

    # Skip if AUDIT_ENABLED=False
    if not getattr(self, "AUDIT_ENABLED", False):
        return result

    ctx = get_normalized_context()

    if is_new:
        # CREATE diff
        changes = {f.name: {"old": None, "new": getattr(self, f.name)} for f in self._meta.fields}

        AuditService.log_create_sync(
            instance=self,
            changes=changes,
            actor_id=ctx["actor_id"],
            actor_email=ctx["actor_email"],
            trace_id=ctx["trace_id"],
            correlation_id=ctx["correlation_id"],
            session_key=ctx["session_key"],
            object_representation=str(self),
            ip_address=ctx["ip_address"],
            user_agent=ctx["user_agent"],
        )

    else:
        # UPDATE diff
        diff = {}
        if old:
            for f in self._meta.fields:
                name = f.name
                old_val = getattr(old, name)
                new_val = getattr(self, name)
                if old_val != new_val:
                    diff[name] = {"old": old_val, "new": new_val}

            AuditService.log_update_sync(
                instance=self,
                changes=diff,
                actor_id=ctx["actor_id"],
                actor_email=ctx["actor_email"],
                trace_id=ctx["trace_id"],
                correlation_id=ctx["correlation_id"],
                session_key=ctx["session_key"],
                object_representation=str(self),
                ip_address=ctx["ip_address"],
                user_agent=ctx["user_agent"],
            )

    return result


def audited_delete(self, *args, **kwargs):
    result = self.__original_delete__(*args, **kwargs)

    if not getattr(self, "AUDIT_ENABLED", False):
        return result

    ctx = get_normalized_context()

    AuditService.log_delete_sync(
        instance=self,
        actor_id=ctx["actor_id"],
        actor_email=ctx["actor_email"],
        trace_id=ctx["trace_id"],
        correlation_id=ctx["correlation_id"],
        session_key=ctx["session_key"],
        object_representation=str(self),
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )

    return result


def audited_update(self, **kwargs):
    model = self.model

    # skip if auditing disabled
    if not getattr(model, "AUDIT_ENABLED", False):
        return self.__original_update__(**kwargs)

    # before snapshot (Sync)
    before = list(self._clone().all())

    # actual update
    updated_count = self.__original_update__(**kwargs)

    if updated_count == 0:
        return updated_count

    # after snapshot (Sync)
    after = list(self._clone().all())

    ctx = get_normalized_context()

    for old_obj, new_obj in zip(before, after):
        diff = {}
        for f in model._meta.fields:
            name = f.name
            old_val = getattr(old_obj, name)
            new_val = getattr(new_obj, name)
            if old_val != new_val:
                diff[name] = {"old": old_val, "new": new_val}

        AuditService.log_update_sync(
            instance=new_obj,
            changes=diff,
            actor_id=ctx["actor_id"],
            actor_email=ctx["actor_email"],
            trace_id=ctx["trace_id"],
            correlation_id=ctx["correlation_id"],
            session_key=ctx["session_key"],
            object_representation=str(new_obj),
            ip_address=ctx["ip_address"],
            user_agent=ctx["user_agent"],
        )

    return updated_count


def audited_delete_queryset(self, **kwargs):
    model = self.model

    # Skip non-audited models
    if not getattr(model, "AUDIT_ENABLED", False):
        return self.__original_delete_queryset__(**kwargs)

    # BEFORE SNAPSHOT (Sync)
    before_instances = list(self._clone().all())

    # ACTUAL DELETE
    deleted_count, details = self.__original_delete_queryset__(**kwargs)

    if deleted_count == 0:
        return deleted_count, details

    ctx = get_normalized_context()

    # CREATE DELETE AUDIT ENTRY FOR EACH ROW
    for inst in before_instances:
        AuditService.log_delete_sync(
            instance=inst,
            actor_id=ctx["actor_id"],
            actor_email=ctx["actor_email"],
            trace_id=ctx["trace_id"],
            correlation_id=ctx["correlation_id"],
            session_key=ctx["session_key"],
            object_representation=str(inst),
            ip_address=ctx["ip_address"],
            user_agent=ctx["user_agent"],
        )

    return deleted_count, details
