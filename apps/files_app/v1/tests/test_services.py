import json
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.errors import HttpError

from apps.files_app.v1.services import FileService


class TestFileService:
    @patch("apps.files_app.v1.services.get_request_logger")
    def test_validate_file_size_success(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        # 1KB file, limit 25KB
        content = b"a" * 1024
        file = SimpleUploadedFile("test.txt", content)
        FileService.validate_file_size(file, limit_kb=25)  # Should not raise

        mock_logger.info.assert_any_call("[1] Entering FileService.validate_file_size with file: test.txt")

    @patch("apps.files_app.v1.services.get_request_logger")
    def test_validate_file_size_exceeded(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        # 26KB file, limit 25KB
        content = b"a" * (26 * 1024)
        file = SimpleUploadedFile("test.txt", content)
        with pytest.raises(HttpError) as exc:
            FileService.validate_file_size(file, limit_kb=25)
        assert exc.value.status_code == 400
        assert "File size exceeds the limit" in str(exc.value)

        mock_logger.info.assert_any_call(
            f"[1] Entering FileService.validate_file_size with file: {file.name}"
        )
        mock_logger.info.assert_any_call(f"[2] File size {len(content)} exceeds limit 25KB")

    def test_get_human_readable_size(self):
        assert FileService.get_human_readable_size(500) == "500.0 B"
        assert FileService.get_human_readable_size(1024) == "1.0 KB"
        assert FileService.get_human_readable_size(1536) == "1.5 KB"
        assert FileService.get_human_readable_size(1024 * 1024) == "1.0 MB"
        assert FileService.get_human_readable_size(1024 * 1024 * 1024) == "1.0 GB"
        assert FileService.get_human_readable_size(1024**5) == "1.0 PB"

    @patch("apps.files_app.v1.services.get_request_logger")
    def test_parse_linear_file_csv(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        content = b"name,age\nAlice,30\nBob,25"
        file = SimpleUploadedFile("test.csv", content, content_type="text/csv")
        data = FileService.parse_linear_file(file)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["age"] == "25"

        mock_logger.info.assert_any_call("[1] Entering FileService.parse_linear_file")
        mock_logger.info.assert_any_call("[2] Parsing CSV file")

    @patch("apps.files_app.v1.services.get_request_logger")
    def test_parse_linear_file_json(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        content = json.dumps([{"name": "Alice", "age": 30}]).encode("utf-8")
        file = SimpleUploadedFile("test.json", content, content_type="application/json")
        data = FileService.parse_linear_file(file)
        assert len(data) == 1
        assert data[0]["name"] == "Alice"

        mock_logger.info.assert_any_call("[1] Entering FileService.parse_linear_file")
        mock_logger.info.assert_any_call("[2] Parsing JSON file")

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

    @patch("apps.files_app.v1.services.get_request_logger")
    def test_parse_linear_file_unsupported_extension(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        content = b"some content"
        file = SimpleUploadedFile("test.txt", content, content_type="text/plain")
        with pytest.raises(HttpError) as exc:
            FileService.parse_linear_file(file)
        assert exc.value.status_code == 400
        assert "Unsupported file type" in str(exc.value)

        mock_logger.info.assert_any_call("[1] Entering FileService.parse_linear_file")
        mock_logger.info.assert_any_call("[3] Unsupported file type: txt")

    @patch("apps.files_app.v1.services.get_request_logger")
    def test_logging_no_logger(self, mock_get_logger):
        """Test that methods run safely when logger is None (e.g. outside request)."""
        mock_get_logger.return_value = None

        # 1. Validate file size (should not crash)
        content = b"a" * 1024
        file = SimpleUploadedFile("test.txt", content)
        FileService.validate_file_size(file, limit_kb=25)

        # 2. Parse file (should not crash)
        content_csv = b"name,age\nAlice,30"
        file_csv = SimpleUploadedFile("test.csv", content_csv, content_type="text/csv")
        data = FileService.parse_linear_file(file_csv)
        assert len(data) == 1

        # 3. Parse JSON file (should not crash)
        content_json = json.dumps([{"name": "Alice", "age": 30}]).encode("utf-8")
        file_json = SimpleUploadedFile("test.json", content_json, content_type="application/json")
        data = FileService.parse_linear_file(file_json)
        assert len(data) == 1

        # 4. File size exceeded with no logger (should not crash but raise HttpError)
        large_content = b"a" * (26 * 1024)
        large_file = SimpleUploadedFile("large.txt", large_content)
        with pytest.raises(HttpError):
            FileService.validate_file_size(large_file, limit_kb=25)

        # 5. Unsupported file with no logger (should not crash)
        file_txt = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        with pytest.raises(HttpError):
            FileService.parse_linear_file(file_txt)

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
