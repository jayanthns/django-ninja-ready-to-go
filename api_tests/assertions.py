from typing import Any


def assert_structure(data: Any, expected_structure: Any, path: str = ""):
    """
    Recursively asserts that data matches the expected_structure.
    expected_structure can be:
    - A type (e.g., str, int, float, bool) or tuple of types
    - A dict {key: expected_val} (checks keys and values)
    - A list [expected_val] (checks that all items in data list match expected_val)
    - A specific value (e.g. "success")
    """

    # Handle Type matching (including tuples for Union)
    if isinstance(expected_structure, type) or (
        isinstance(expected_structure, tuple) and all(isinstance(x, type) for x in expected_structure)
    ):
        assert isinstance(
            data, expected_structure
        ), f"Type mismatch at {path}: expected {expected_structure}, got {type(data).__name__} ({data})"
        return

    # Handle Dict matching
    if isinstance(expected_structure, dict):
        assert isinstance(data, dict), f"Type mismatch at {path}: expected dict, got {type(data).__name__}"

        # Check all expected keys are present
        for key, val in expected_structure.items():
            assert key in data, f"Missing key '{key}' at {path}"
            assert_structure(data[key], val, path=f"{path}.{key}")

        # Check no unexpected keys are present (Strictness)
        for key in data.keys():
            assert key in expected_structure, f"Unexpected key '{key}' at {path}"

        return

    # Handle List matching
    if isinstance(expected_structure, list):
        assert isinstance(data, list), f"Type mismatch at {path}: expected list, got {type(data).__name__}"
        if not expected_structure:
            # If expected is [], we might allow any list? Or empty list?
            # Let's assume [] means empty list.
            assert len(data) == 0, f"Expected empty list at {path}, got {len(data)} items"
        else:
            # Assume list has one item defining the structure of elements
            element_structure = expected_structure[0]
            for i, item in enumerate(data):
                assert_structure(item, element_structure, path=f"{path}[{i}]")
        return

    # Handle exact value matching (e.g. None or specific strings)
    assert data == expected_structure, f"Value mismatch at {path}: expected {expected_structure}, got {data}"
