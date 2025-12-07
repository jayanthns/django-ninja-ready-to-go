from .patcher import AuditPatcher

audited_asave = AuditPatcher.asave
audited_adelete = AuditPatcher.adelete
audited_acreate = AuditPatcher.acreate
audited_aupdate = AuditPatcher.aupdate
audited_adelete_queryset = AuditPatcher.adelete_queryset

audited_save = AuditPatcher.save
audited_delete = AuditPatcher.delete
audited_update = AuditPatcher.update
audited_delete_queryset = AuditPatcher.delete_queryset
