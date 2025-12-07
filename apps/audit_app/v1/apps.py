from django.apps import AppConfig, apps


class AuditAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit_app.v1"
    label = "apps_audit_app_v1"

    def ready(self):
        self._patch_methods()

    def _patch_methods(self):
        from .patch import (
            audited_acreate,
            audited_adelete,
            audited_adelete_queryset,
            audited_asave,
            audited_aupdate,
            audited_delete,
            audited_delete_queryset,
            audited_save,
            audited_update,
        )

        for model in apps.get_models():

            # Skip models not audited
            if not getattr(model, "AUDIT_ENABLED", False):
                continue

            # ──────────────────────────────────────────────
            # 1️⃣ PATCH model.asave() AND model.save()
            # ──────────────────────────────────────────────
            if hasattr(model, "asave") and not hasattr(model, "__original_asave__"):
                model.__original_asave__ = model.asave
                model.asave = audited_asave

            if hasattr(model, "save") and not hasattr(model, "__original_save__"):
                model.__original_save__ = model.save
                model.save = audited_save

            # ──────────────────────────────────────────────
            # 2️⃣ PATCH model.adelete() AND model.delete()
            # ──────────────────────────────────────────────
            if hasattr(model, "adelete") and not hasattr(model, "__original_adelete__"):
                model.__original_adelete__ = model.adelete
                model.adelete = audited_adelete

            if hasattr(model, "delete") and not hasattr(model, "__original_delete__"):
                model.__original_delete__ = model.delete
                model.delete = audited_delete

            # ──────────────────────────────────────────────
            # 3️⃣ PATCH manager.acreate()
            # (manager-level, because acreate is on manager)
            # ──────────────────────────────────────────────
            manager = model.objects.__class__
            if hasattr(manager, "acreate") and not hasattr(manager, "__original_acreate__"):
                manager.__original_acreate__ = manager.acreate
                manager.acreate = audited_acreate

            # ──────────────────────────────────────────────
            # 4️⃣ PATCH queryset.aupdate() AND queryset.update()
            # ──────────────────────────────────────────────
            # Get the queryset class for this model
            qs_class = model.objects._queryset_class

            if hasattr(qs_class, "aupdate") and not hasattr(qs_class, "__original_aupdate__"):
                qs_class.__original_aupdate__ = qs_class.aupdate
                qs_class.aupdate = audited_aupdate

            if hasattr(qs_class, "update") and not hasattr(qs_class, "__original_update__"):
                qs_class.__original_update__ = qs_class.update
                qs_class.update = audited_update

            # ──────────────────────────────────────────────
            # 5️⃣ PATCH queryset.adelete() AND queryset.delete()
            # ──────────────────────────────────────────────
            if hasattr(qs_class, "adelete") and not hasattr(qs_class, "__original_adelete_queryset__"):
                qs_class.__original_adelete_queryset__ = qs_class.adelete
                qs_class.adelete = audited_adelete_queryset

            if hasattr(qs_class, "delete") and not hasattr(qs_class, "__original_delete_queryset__"):
                # Note: We map queryset.delete to audited_delete_queryset
                # But we must be careful not to confuse it with model.delete
                # The queryset class attribute 'delete' is distinct from model 'delete'
                qs_class.__original_delete_queryset__ = qs_class.delete
                qs_class.delete = audited_delete_queryset
