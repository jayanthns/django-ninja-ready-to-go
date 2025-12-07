import inspect

from apps.audit_app.v1 import patch
from apps.audit_app.v1.patcher import AuditPatcher


class TestPatchExports:

    def test_exported_names_exist(self):
        """Ensure all expected re-exported symbols exist."""
        expected = [
            "audited_asave",
            "audited_adelete",
            "audited_acreate",
            "audited_aupdate",
            "audited_adelete_queryset",
            "audited_save",
            "audited_delete",
            "audited_update",
            "audited_delete_queryset",
        ]

        for name in expected:
            assert hasattr(patch, name), f"{name} is missing in patch.py"

    def test_async_exports_are_coroutine_functions(self):
        """Ensure async patches really point to coroutine functions."""
        async_names = [
            "audited_asave",
            "audited_adelete",
            "audited_acreate",
            "audited_aupdate",
            "audited_adelete_queryset",
        ]

        for name in async_names:
            func = getattr(patch, name)
            assert inspect.iscoroutinefunction(func), f"{name} must be async"

            # Must be the same underlying AuditPatcher function
            patcher_func = getattr(AuditPatcher, name.replace("audited_", ""))
            assert func is patcher_func, f"{name} does not point to AuditPatcher.{patcher_func.__name__}"

    def test_sync_exports_are_regular_functions(self):
        """Ensure synchronous patches are normal functions."""
        sync_names = [
            "audited_save",
            "audited_delete",
            "audited_update",
            "audited_delete_queryset",
        ]

        for name in sync_names:
            func = getattr(patch, name)
            assert callable(func), f"{name} must be callable"
            assert not inspect.iscoroutinefunction(func), f"{name} must NOT be async"

            # must reference the AuditPatcher implementation
            patcher_func = getattr(AuditPatcher, name.replace("audited_", ""))
            assert func is patcher_func, f"{name} does not reference AuditPatcher.{patcher_func.__name__}"

    def test_no_extra_exports(self):
        """Ensure only expected attributes are exported (safety check)."""
        allowed = {
            "audited_asave",
            "audited_adelete",
            "audited_acreate",
            "audited_aupdate",
            "audited_adelete_queryset",
            "audited_save",
            "audited_delete",
            "audited_update",
            "audited_delete_queryset",
        }

        exported = {name for name in dir(patch) if name.startswith("audited_")}

        assert exported == allowed, f"Unexpected exports found: {exported - allowed}"
