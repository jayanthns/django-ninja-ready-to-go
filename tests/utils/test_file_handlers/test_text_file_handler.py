import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.file_handlers import TextFileHandler  # adjust import to your path


@pytest.mark.usefixtures("tmp_path")
class TestTextFileHandler:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path):
        """Common setup: temporary file path."""
        self.tmp_path = tmp_path

    # -------------------------
    # Initialization Tests
    # -------------------------
    @patch("src.utils.file_handlers.get_logger_with_trace")
    def test_init_uses_default_logger(self, mock_get_logger):
        fake_logger = MagicMock()
        mock_get_logger.return_value = fake_logger

        handler = TextFileHandler(file_path="sample.txt", logger=None, trace_id=None)

        assert handler.logger == fake_logger
        assert isinstance(uuid.UUID(handler.trace_id), uuid.UUID)
        mock_get_logger.assert_called_once()

    def test_init_with_custom_logger(self):
        mock_logger = MagicMock()
        trace_id = str(uuid.uuid4())
        handler = TextFileHandler(file_path="file.txt", logger=mock_logger, trace_id=trace_id)

        assert handler.logger == mock_logger
        assert handler.file_path.name == "file.txt"
        assert handler.trace_id == trace_id

    # -------------------------
    # Read / Write Tests
    # -------------------------
    def test_write_and_read_success(self):
        """Write a string to file and read it back, check logging."""
        file_path = self.tmp_path / "test.txt"
        mock_logger = MagicMock()
        handler = TextFileHandler(file_path, logger=mock_logger, trace_id=None)

        content = "Hello, World!\nThis is a test."
        handler.write(content)

        # Validate written content
        read_content = handler.read()
        assert read_content == content

        # Logging assertions for write
        mock_logger.info.assert_called()
        write_log = mock_logger.info.call_args_list[0][0][0]
        assert "TextFileHandler.write succeeded" in write_log
        assert str(file_path) in write_log
        assert "chars=" in write_log
        assert "elapsed_ms" in write_log
        assert "success=True" in write_log

        # Logging assertions for read
        read_log = mock_logger.info.call_args_list[1][0][0]
        assert "TextFileHandler.read succeeded" in read_log
        assert str(file_path) in read_log
        assert "file_size" in read_log
        assert "elapsed_ms" in read_log
        assert "success=True" in read_log

    def test_read_failure_file_missing(self):
        """Reading non-existent file should raise FileNotFoundError and log failure."""
        file_path = self.tmp_path / "missing.txt"
        mock_logger = MagicMock()
        handler = TextFileHandler(file_path, logger=mock_logger, trace_id=None)

        with pytest.raises(FileNotFoundError):
            handler.read()

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "TextFileHandler.read failed" in log_data
        assert "FileNotFoundError" in log_data or "No such file" in log_data
        assert "success=False" in log_data

    def test_write_failure_permission_error(self):
        """Simulate write permission error and assert logging."""
        file_path = self.tmp_path / "readonly.txt"
        mock_logger = MagicMock()
        handler = TextFileHandler(file_path, logger=mock_logger, trace_id=None)

        with patch("src.utils.file_handlers.open", side_effect=PermissionError("Access denied")):
            import pytest

            with pytest.raises(PermissionError):
                handler.write("some content")

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "TextFileHandler.write failed" in log_data
        assert "error" in log_data
        assert "success=False" in log_data
