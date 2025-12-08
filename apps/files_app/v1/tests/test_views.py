import json
import uuid
from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.files_app.v1.views import (
    download_file,
    preview_file,
    stream_file,
    upload_generic_file,
    upload_linear_file,
)


class TestFilesAppViews:
    @pytest.fixture
    def mock_request(self):
        """Mock a minimal Django-Ninja style request."""
        mock = MagicMock()
        mock.trace_id = uuid.uuid4()
        mock.logger = MagicMock()
        return mock

    def test_upload_linear_csv_success(self, mock_request):
        content = b"name,age\nAlice,30\nBob,25"
        file = SimpleUploadedFile("test.csv", content, content_type="text/csv")

        response = upload_linear_file(mock_request, file=file)

        assert response["data"]["total_rows"] == 2
        assert response["data"]["preview_rows"][0]["name"] == "Alice"
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["error"] == {}

        mock_request.logger.info.assert_any_call("[1] Entering upload_linear_file")
        mock_request.logger.info.assert_any_call("[2] Validating file size")
        mock_request.logger.info.assert_any_call("[3] Parsing file")
        mock_request.logger.info.assert_any_call("[4] Exiting upload_linear_file")

    def test_upload_linear_json_success(self, mock_request):
        content = json.dumps([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]).encode("utf-8")
        file = SimpleUploadedFile("test.json", content, content_type="application/json")

        response = upload_linear_file(mock_request, file=file)

        assert response["data"]["total_rows"] == 2
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["error"] == {}

        mock_request.logger.info.assert_any_call("[1] Entering upload_linear_file")
        mock_request.logger.info.assert_any_call("[2] Validating file size")
        mock_request.logger.info.assert_any_call("[3] Parsing file")
        mock_request.logger.info.assert_any_call("[4] Exiting upload_linear_file")

    def test_upload_linear_file_too_large(self, mock_request):
        # 26KB file (limit is 25KB)
        content = b"a" * (26 * 1024)
        file = SimpleUploadedFile("large.csv", content, content_type="text/csv")

        status, response = upload_linear_file(mock_request, file=file)

        assert status == 400
        assert response["data"] is None
        assert "File size exceeds the limit" in response["error"]["message"]
        assert response["trace_id"] == str(mock_request.trace_id)

        mock_request.logger.info.assert_any_call("[1] Entering upload_linear_file")
        mock_request.logger.info.assert_any_call("[2] Validating file size")
        # Ensure error log contains the message
        # The specific message depends on exception str(e) which includes status code sometimes or just valid/invalid
        # We'll assert partial match if needed, or exact if predictable
        # HttpError str() is usually something like "File size exceeds..."
        mock_request.logger.info.assert_any_call(
            "[5] Error in upload_linear_file: File size exceeds the limit of 25KB. Current size: 26.00KB"
        )

    def test_upload_generic_file_success(self, mock_request):
        content = b"some generic content"
        file = SimpleUploadedFile("test.txt", content, content_type="text/plain")

        response = upload_generic_file(mock_request, file=file)

        assert response["data"]["filename"] == "test.txt"
        assert response["data"]["size"] == len(content)
        assert response["data"]["human_readable_size"] == "20.0 B"
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["error"] == {}

        mock_request.logger.info.assert_any_call("[1] Entering upload_generic_file")
        mock_request.logger.info.assert_any_call("[2] Validating file size")
        mock_request.logger.info.assert_any_call("[3] Exiting upload_generic_file")

    def test_upload_generic_file_too_large(self, mock_request):
        # 26KB file (limit is 25KB)
        content = b"a" * (26 * 1024)
        file = SimpleUploadedFile("large.txt", content, content_type="text/plain")

        status, response = upload_generic_file(mock_request, file=file)

        assert status == 400
        assert response["data"] is None
        assert "File size exceeds the limit" in response["error"]["message"]
        assert response["trace_id"] == str(mock_request.trace_id)

        mock_request.logger.info.assert_any_call("[1] Entering upload_generic_file")
        mock_request.logger.info.assert_any_call(
            "[4] Error in upload_generic_file: File size exceeds the limit of 25KB. Current size: 26.00KB"
        )

    def test_download_file(self, mock_request):
        filename = "test.txt"
        response = download_file(mock_request, filename=filename)

        assert response.status_code == 200
        assert response["Content-Disposition"] == f'attachment; filename="{filename}"'
        assert response.content  # Verify content exists

        mock_request.logger.info.assert_any_call(f"[1] Entering download_file: {filename}")
        mock_request.logger.info.assert_any_call("[2] Exiting download_file")

    def test_stream_file(self, mock_request):
        filename = "test.txt"
        response = stream_file(mock_request, filename=filename)

        assert response.status_code == 200
        assert response.streaming is True
        assert response["Content-Disposition"] == f'attachment; filename="{filename}"'

        mock_request.logger.info.assert_any_call(f"[1] Entering stream_file: {filename}")
        mock_request.logger.info.assert_any_call("[2] Exiting stream_file")

    def test_preview_file(self, mock_request):
        filename = "test.txt"
        response = preview_file(mock_request, filename=filename)

        assert response.status_code == 200
        assert response.content  # Verify content exists

        mock_request.logger.info.assert_any_call(f"[1] Entering preview_file: {filename}")
        mock_request.logger.info.assert_any_call("[2] Exiting preview_file")
