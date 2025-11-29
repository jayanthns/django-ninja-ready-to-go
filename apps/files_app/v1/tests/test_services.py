import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.errors import HttpError

from apps.files_app.v1.services import FileService


class TestFileService:
    def test_validate_file_size_success(self):
        # 1KB file, limit 25KB
        content = b"a" * 1024
        file = SimpleUploadedFile("test.txt", content)
        FileService.validate_file_size(file, limit_kb=25)  # Should not raise

    def test_validate_file_size_exceeded(self):
        # 26KB file, limit 25KB
        content = b"a" * (26 * 1024)
        file = SimpleUploadedFile("test.txt", content)
        with pytest.raises(HttpError) as exc:
            FileService.validate_file_size(file, limit_kb=25)
        assert exc.value.status_code == 400
        assert "File size exceeds the limit" in str(exc.value)

    def test_get_human_readable_size(self):
        assert FileService.get_human_readable_size(500) == "500.0 B"
        assert FileService.get_human_readable_size(1024) == "1.0 KB"
        assert FileService.get_human_readable_size(1536) == "1.5 KB"
        assert FileService.get_human_readable_size(1024 * 1024) == "1.0 MB"
        assert FileService.get_human_readable_size(1024 * 1024 * 1024) == "1.0 GB"
        assert FileService.get_human_readable_size(1024**5) == "1.0 PB"

    def test_parse_linear_file_csv(self):
        content = b"name,age\nAlice,30\nBob,25"
        file = SimpleUploadedFile("test.csv", content, content_type="text/csv")
        data = FileService.parse_linear_file(file)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["age"] == "25"

    def test_parse_linear_file_json(self):
        content = json.dumps([{"name": "Alice", "age": 30}]).encode("utf-8")
        file = SimpleUploadedFile("test.json", content, content_type="application/json")
        data = FileService.parse_linear_file(file)
        assert len(data) == 1
        assert data[0]["name"] == "Alice"

    def test_parse_linear_file_invalid_json(self):
        content = b"invalid json"
        file = SimpleUploadedFile("test.json", content, content_type="application/json")
        with pytest.raises(HttpError) as exc:
            FileService.parse_linear_file(file)
        assert exc.value.status_code == 400
        assert "Invalid JSON file" in str(exc.value)

    def test_parse_linear_file_json_not_list(self):
        content = json.dumps({"name": "Alice"}).encode("utf-8")
        file = SimpleUploadedFile("test.json", content, content_type="application/json")
        with pytest.raises(HttpError) as exc:
            FileService.parse_linear_file(file)
        assert exc.value.status_code == 400
        assert "JSON file must contain a list of objects" in str(exc.value)

    def test_parse_linear_file_unsupported_extension(self):
        content = b"some content"
        file = SimpleUploadedFile("test.txt", content, content_type="text/plain")
        with pytest.raises(HttpError) as exc:
            FileService.parse_linear_file(file)
        assert exc.value.status_code == 400
        assert "Unsupported file type" in str(exc.value)

    def test_get_dummy_content(self):
        content = FileService.get_dummy_content(size_kb=1)
        # It's approximate, but should be close to 1024 bytes
        assert len(content.encode("utf-8")) > 0

    def test_get_file_content(self):
        content = FileService.get_file_content("test.txt", size_kb=1)
        assert len(content) > 0

    def test_get_file_stream(self):
        stream = FileService.get_file_stream("test.txt", size_kb=1)
        chunks = list(stream)
        assert len(chunks) > 0
        assert isinstance(chunks[0], str)
