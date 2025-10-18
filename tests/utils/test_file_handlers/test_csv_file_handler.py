import csv
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.file_handlers import CSVFileHandler  # adjust import to your actual path


@pytest.mark.usefixtures("tmp_path")
class TestCSVFileHandler:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path):
        """Common setup: temporary file path."""
        self.tmp_path = tmp_path

    # -------------------------
    # Base Initialization Tests
    # -------------------------
    @patch("src.utils.file_handlers.get_logger_with_trace")
    def test_init_uses_default_logger(self, mock_get_logger):
        """Should call get_logger_with_trace when no logger is provided."""
        fake_logger = MagicMock()
        mock_get_logger.return_value = fake_logger

        handler = CSVFileHandler(file_path="sample.csv", logger=None, trace_id=None)

        assert handler.logger == fake_logger
        assert isinstance(uuid.UUID(handler.trace_id), uuid.UUID)
        mock_get_logger.assert_called_once()

    def test_init_with_custom_logger(self):
        """Should use custom logger and trace_id if provided."""
        mock_logger = MagicMock()
        trace_id = str(uuid.uuid4())
        handler = CSVFileHandler(file_path="file.csv", logger=mock_logger, trace_id=trace_id)

        assert handler.logger == mock_logger
        assert handler.file_path.name == "file.csv"
        assert handler.trace_id == trace_id

    # -------------------------
    # Read / Write Tests
    # -------------------------
    def test_write_and_read_success(self):
        """Write CSV data and read it back."""
        file_path = self.tmp_path / "test.csv"
        mock_logger = MagicMock()
        handler = CSVFileHandler(file_path, logger=mock_logger, trace_id=None)

        data = [
            {"name": "Alice", "age": "25"},
            {"name": "Bob", "age": "30"},
        ]

        # Write CSV
        handler.write(data)

        # Validate file content
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            result = [row for row in reader]
        assert result == data

        # Logging assertions for write
        mock_logger.info.assert_called()
        log_data = mock_logger.info.call_args[0][0]
        assert "CSVFileHandler.write succeeded" in log_data
        assert "rows=2" in log_data
        assert str(file_path) in log_data
        assert "elapsed_ms" in log_data
        assert "success=True" in log_data

        # Reset mock to test read logging
        mock_logger.reset_mock()

        # Read CSV
        read_data = handler.read()
        assert read_data == data

        # Logging assertions for read
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "CSVFileHandler.read succeeded" in log_data
        assert "rows=2" in log_data
        assert str(file_path) in log_data
        assert "elapsed_ms" in log_data
        assert "success=True" in log_data

    def test_write_failure_empty_data(self):
        """Writing empty data should raise ValueError and log failure."""
        file_path = self.tmp_path / "empty.csv"
        mock_logger = MagicMock()
        handler = CSVFileHandler(file_path, logger=mock_logger, trace_id=None)

        with pytest.raises(ValueError):
            handler.write([])

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "CSVFileHandler.write failed" in log_data
        assert "error='No data to write to CSV'" in log_data or "No data to write" in log_data
        assert "success=False" in log_data

    def test_read_failure_file_missing(self):
        """Reading non-existent file should raise FileNotFoundError and log failure."""
        file_path = self.tmp_path / "missing.csv"
        mock_logger = MagicMock()
        handler = CSVFileHandler(file_path, logger=mock_logger, trace_id=None)

        with pytest.raises(FileNotFoundError):
            handler.read()

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "CSVFileHandler.read failed" in log_data
        assert "FileNotFoundError" in log_data or "No such file" in log_data
        assert "success=False" in log_data

    def test_write_failure_permission_error(self):
        """Simulate write permission error and assert failure logging."""
        file_path = self.tmp_path / "readonly.csv"
        mock_logger = MagicMock()
        handler = CSVFileHandler(file_path, logger=mock_logger, trace_id=None)

        # Patch the open inside CSVFileHandler
        with patch("src.utils.file_handlers.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                handler.write([{"name": "Alice"}])

        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "CSVFileHandler.write failed" in log_data
        assert "error" in log_data
        assert "success=False" in log_data
