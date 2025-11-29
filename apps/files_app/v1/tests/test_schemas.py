import pytest
from pydantic import ValidationError

from apps.files_app.v1.schemas import FileSuccessSchema, LinearDataResponseSchema


class TestSchemas:
    def test_file_success_schema_valid(self):
        data = {"message": "Success", "filename": "test.txt", "size": 1024, "human_readable_size": "1.0 KB"}
        schema = FileSuccessSchema(**data)
        assert schema.message == "Success"
        assert schema.filename == "test.txt"
        assert schema.size == 1024
        assert schema.human_readable_size == "1.0 KB"

    def test_file_success_schema_invalid(self):
        data = {
            "message": "Success",
            # Missing filename, size, human_readable_size
        }
        with pytest.raises(ValidationError):
            FileSuccessSchema(**data)

    def test_linear_data_response_schema_valid(self):
        data = {
            "message": "Success",
            "filename": "test.csv",
            "total_rows": 10,
            "preview_rows": [{"name": "Alice"}, {"name": "Bob"}],
        }
        schema = LinearDataResponseSchema(**data)
        assert schema.message == "Success"
        assert schema.total_rows == 10
        assert len(schema.preview_rows) == 2

    def test_linear_data_response_schema_invalid(self):
        data = {
            "message": "Success",
            "filename": "test.csv",
            "total_rows": "not an int",  # Invalid type
            "preview_rows": [],
        }
        with pytest.raises(ValidationError):
            LinearDataResponseSchema(**data)
