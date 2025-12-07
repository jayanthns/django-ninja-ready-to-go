from unittest.mock import MagicMock

from apps.audit_app.v1.patch_utils import safe_patch


class TestSafePatch:

    def test_no_method_on_target_does_nothing(self):
        """safe_patch should exit silently when the method does not exist."""

        class Empty:
            pass

        target = Empty()

        # Ensure the method does NOT exist
        assert not hasattr(target, "missing_method")

        safe_patch(target, "missing_method", new_impl=lambda x: x)

        # Should not create or modify anything
        assert not hasattr(target, "__original_missing_method__")
        assert not hasattr(target, "missing_method")

    def test_patches_method_when_not_patched_before(self):
        """safe_patch should store the original and patch the method."""
        target = MagicMock()

        # define a fake method
        def old_method():
            return "old"

        target.existing = old_method

        # new implementation
        def new_method():
            return "new"

        safe_patch(target, "existing", new_method)

        # ensure __original_existing__ stored
        assert hasattr(target, "__original_existing__")
        assert target.__original_existing__ is old_method

        # ensure method replaced
        assert target.existing is new_method

    def test_does_not_patch_if_already_patched(self):
        """safe_patch should skip if __original_method__ already exists."""
        target = MagicMock()

        def old_method():
            return "old"

        def patched_method():
            return "patched"

        target.existing = old_method

        # Mimic already patched
        target.__original_existing__ = old_method

        safe_patch(target, "existing", patched_method)

        # Should NOT replace
        assert target.existing is old_method
        assert target.__original_existing__ is old_method

    def test_safe_patch_does_not_override_original_method_twice(self):
        """Original method should remain unchanged even after repeated safe_patch calls."""
        target = MagicMock()

        def original():
            return "original"

        def replacement():
            return "replacement"

        target.save = original

        # First patch
        safe_patch(target, "save", replacement)

        # Try patching again
        safe_patch(target, "save", lambda: "another")

        # Should still point to first replacement
        assert target.save is replacement

        # Original method must remain unchanged
        assert target.__original_save__ is original

    def test_safe_patch_stores_original_before_replacing(self):
        """Ensure stored __original_method__ and patched method are correct."""
        target = MagicMock()

        def original_handler():
            return "original"

        def patched_handler():
            return "patched"

        target.handle = original_handler

        safe_patch(target, "handle", patched_handler)

        # original method stored
        assert hasattr(target, "__original_handle__")
        assert target.__original_handle__ is original_handler

        # new method applied
        assert target.handle is patched_handler

    def test_safe_patch_does_not_modify_unrelated_attributes(self):
        """Ensure safe_patch only changes the target method, not other attrs."""
        target = MagicMock()
        target.foo = "bar"

        def old_method():
            return "old"

        def new_method():
            return "new"

        target.existing = old_method

        safe_patch(target, "existing", new_method)

        # unrelated attribute unaffected
        assert target.foo == "bar"
