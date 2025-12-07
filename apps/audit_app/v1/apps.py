from django.apps import AppConfig, apps


class AuditAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit_app.v1"
    label = "apps_audit_app_v1"

    def ready(self):
        self._patch_methods()

    def _patch_methods(self):
        from .patch_utils import safe_patch  # noqa
        from .patcher import AuditPatcher  # noqa

        for model in apps.get_models():

            if not getattr(model, "AUDIT_ENABLED", False):
                continue

            # ---------------------------------------------------------
            # 1️⃣ INSTANCE-LEVEL METHODS
            # ---------------------------------------------------------
            safe_patch(model, "asave", AuditPatcher.asave)
            safe_patch(model, "save", AuditPatcher.save)
            safe_patch(model, "adelete", AuditPatcher.adelete)
            safe_patch(model, "delete", AuditPatcher.delete)

            # ---------------------------------------------------------
            # 2️⃣ MANAGER-LEVEL METHODS
            # ---------------------------------------------------------
            manager = model.objects.__class__
            safe_patch(manager, "acreate", AuditPatcher.acreate)

            # ---------------------------------------------------------
            # 3️⃣ QUERYSET-LEVEL METHODS
            # ---------------------------------------------------------
            qs_class = model.objects._queryset_class

            safe_patch(qs_class, "aupdate", AuditPatcher.aupdate)
            safe_patch(qs_class, "update", AuditPatcher.update)
            safe_patch(qs_class, "adelete", AuditPatcher.adelete_queryset)
            safe_patch(qs_class, "delete", AuditPatcher.delete_queryset)
