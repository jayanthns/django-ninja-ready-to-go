from django.apps import AppConfig, apps


class AuditAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit_app.v1"
    label = "apps_audit_app_v1"

    def ready(self):
        self._patch_async_methods()

    def _patch_async_methods(self):
        from .patch import (
            audited_acreate,
            audited_adelete,
            audited_adelete_queryset,
            audited_asave,
            audited_aupdate,
        )

        for model in apps.get_models():

            # Skip models not audited
            if not getattr(model, "AUDIT_ENABLED", False):
                continue

            # ──────────────────────────────────────────────
            # 1️⃣ PATCH model.asave()
            # ──────────────────────────────────────────────
            if hasattr(model, "asave") and not hasattr(model, "__original_asave__"):
                model.__original_asave__ = model.asave
                model.asave = audited_asave

            # ──────────────────────────────────────────────
            # 2️⃣ PATCH model.adelete()
            # ──────────────────────────────────────────────
            if hasattr(model, "adelete") and not hasattr(model, "__original_adelete__"):
                model.__original_adelete__ = model.adelete
                model.adelete = audited_adelete

            # ──────────────────────────────────────────────
            # 3️⃣ PATCH manager.acreate()
            # (manager-level, because acreate is on manager)
            # ──────────────────────────────────────────────
            manager = model.objects.__class__
            if hasattr(manager, "acreate") and not hasattr(manager, "__original_acreate__"):
                manager.__original_acreate__ = manager.acreate
                manager.acreate = audited_acreate

            # ──────────────────────────────────────────────
            # 4️⃣ PATCH queryset.aupdate()
            # (THIS is the missing part!!!)
            # ──────────────────────────────────────────────

            # Get the queryset class for this model
            qs_class = model.objects._queryset_class

            if hasattr(qs_class, "aupdate") and not hasattr(qs_class, "__original_aupdate__"):
                qs_class.__original_aupdate__ = qs_class.aupdate
                qs_class.aupdate = audited_aupdate

            # ──────────────────────────────────────────────
            # 5️⃣ PATCH queryset.adelete()
            # ──────────────────────────────────────────────
            qs_class = model.objects._queryset_class

            if hasattr(qs_class, "adelete") and not hasattr(qs_class, "__original_adelete_queryset__"):
                qs_class.__original_adelete_queryset__ = qs_class.adelete
                qs_class.adelete = audited_adelete_queryset
