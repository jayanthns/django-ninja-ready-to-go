from .context import get_context
from .services import AuditService


async def audited_asave(self, *args, **kwargs):
    is_new = self.pk is None

    # BEFORE state
    old = None
    if not is_new:
        old = await self.__class__.objects.aget(pk=self.pk)

    # Perform actual save
    result = await self.__original_asave__(*args, **kwargs)

    # Skip if AUDIT_ENABLED=False
    if not getattr(self, "AUDIT_ENABLED", False):
        return result

    ctx = get_context()

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

    ctx = get_context()

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

    ctx = get_context()

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

    ctx = get_context()

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

    ctx = get_context()

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
