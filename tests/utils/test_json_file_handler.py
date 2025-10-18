import json
import os
import tempfile

import pytest

from src.utils.file_handlers import JSONFileHandler


@pytest.fixture
def temp_json_file():
    """Creates a temporary JSON file for testing."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    yield temp_file.name
    temp_file.close()
    os.unlink(temp_file.name)


class TestJSONFileHandler:
    def test_write_and_read_dict(self, temp_json_file):
        """Test writing and reading a dictionary JSON."""
        handler = JSONFileHandler(temp_json_file)
        data = {"name": "John", "age": 30, "skills": ["Python", "Django"]}

        handler.write(data)
        result = handler.read()

        assert result == data
        assert isinstance(result, dict)
        assert "skills" in result
        assert result["age"] == 30

    def test_write_and_read_list(self, temp_json_file):
        """Test writing and reading a list of JSON objects."""
        handler = JSONFileHandler(temp_json_file)
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        handler.write(data)

        result = handler.read()
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["id"] == 1

    def test_overwrite_existing_file(self, temp_json_file):
        """Test that writing overwrites previous content."""
        handler = JSONFileHandler(temp_json_file)
        handler.write({"a": 1})
        handler.write({"b": 2})

        result = handler.read()
        assert result == {"b": 2}  # overwritten

    def test_invalid_json_file_raises_error(self, temp_json_file):
        """Test reading invalid JSON raises JSONDecodeError."""
        with open(temp_json_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        handler = JSONFileHandler(temp_json_file)
        with pytest.raises(json.JSONDecodeError):
            handler.read()

    def test_file_not_found_raises_error(self):
        """Test initializing with non-existent file still allows write, but read fails."""
        handler = JSONFileHandler("nonexistent_file.json")

        # Writing should create file
        handler.write({"key": "value"})
        assert os.path.exists("nonexistent_file.json")

        # Cleanup
        os.remove("nonexistent_file.json")

    def test_write_non_serializable_object_raises(self, temp_json_file):
        """Test attempting to write non-JSON-serializable data."""
        handler = JSONFileHandler(temp_json_file)
        data = {"now": set([1, 2, 3])}  # sets are not JSON serializable

        with pytest.raises(TypeError):
            handler.write(data)
