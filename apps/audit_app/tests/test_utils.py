from unittest.mock import MagicMock

import pytest

from apps.audit_app.v1.utils import compute_create_diff, compute_delete_diff, compute_update_diff


def make_field(name):
    """Helper to mimic a Django model field."""
    f = MagicMock()
    f.name = name
    return f


def make_instance(field_names, values):
    """
    Creates a fake model instance with:
    - _meta.fields → list of mock fields
    - attributes for each field
    """
    inst = MagicMock()
    fields = [make_field(n) for n in field_names]
    inst._meta.fields = fields

    for name, value in zip(field_names, values):
        setattr(inst, name, value)

    return inst


# ---------------------------------------------------------
#  CREATE DIFF TESTS
# ---------------------------------------------------------
class TestComputeCreateDiff:

    def test_compute_create_diff_basic(self):
        inst = make_instance(["a", "b"], [10, "hello"])

        diff = compute_create_diff(inst)

        assert diff == {
            "a": {"old": None, "new": 10},
            "b": {"old": None, "new": "hello"},
        }

    def test_compute_create_diff_empty_fields(self):
        inst = make_instance([], [])

        diff = compute_create_diff(inst)

        assert diff == {}  # no fields, nothing to report


# ---------------------------------------------------------
#  UPDATE DIFF TESTS
# ---------------------------------------------------------
class TestComputeUpdateDiff:

    def test_compute_update_diff_detects_changes(self):
        old = make_instance(["x", "y"], [1, "same"])
        new = make_instance(["x", "y"], [2, "same"])

        diff = compute_update_diff(old, new)

        assert diff == {
            "x": {"old": 1, "new": 2},
        }  # "y" unchanged → not included

    def test_compute_update_diff_multiple_changes(self):
        old = make_instance(["a", "b", "c"], [1, 2, 3])
        new = make_instance(["a", "b", "c"], [1, 20, 30])

        diff = compute_update_diff(old, new)

        assert diff == {
            "b": {"old": 2, "new": 20},
            "c": {"old": 3, "new": 30},
        }

    def test_compute_update_diff_no_changes(self):
        old = make_instance(["foo"], [100])
        new = make_instance(["foo"], [100])

        diff = compute_update_diff(old, new)

        assert diff == {}  # no changes at all

    def test_compute_update_diff_type_change(self):
        old = make_instance(["val"], ["123"])
        new = make_instance(["val"], [123])

        diff = compute_update_diff(old, new)

        assert diff == {"val": {"old": "123", "new": 123}}


# ---------------------------------------------------------
#  DELETE DIFF TESTS
# ---------------------------------------------------------
class TestComputeDeleteDiff:

    def test_compute_delete_diff_basic(self):
        inst = make_instance(["field1", "field2"], ["data", 999])

        diff = compute_delete_diff(inst)

        assert diff == {
            "field1": {"old": "data", "new": None},
            "field2": {"old": 999, "new": None},
        }

    def test_compute_delete_diff_empty(self):
        inst = make_instance([], [])

        diff = compute_delete_diff(inst)

        assert diff == {}  # nothing to delete
