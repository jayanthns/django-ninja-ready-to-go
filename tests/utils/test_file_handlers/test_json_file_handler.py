import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.file_handlers import JSONFileHandler  # adjust import to your actual path


@pytest.mark.usefixtures("tmp_path")
class TestJSONFileHandler:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path):
        """Common setup: temporary file path."""
        self.tmp_path = tmp_path

    # -------------------------
    # Base Initialization Tests
    # -------------------------
    @patch("src.utils.file_handlers.get_logger_with_trace")
    def test_init_uses_default_logger(self, mock_get_logger):
        """
        Should call get_logger_with_trace when no logger is provided.
        Also tests logging via the returned logger instance.
        """
        # Prepare a fake logger that will capture logging calls
        fake_logger = MagicMock()
        mock_get_logger.return_value = fake_logger

        # Create handler without passing a logger
        handler = JSONFileHandler(file_path="sample.json", logger=None, trace_id=None)

        # Assert logger returned by factory is assigned
        assert handler.logger == fake_logger
        assert isinstance(uuid.UUID(handler.trace_id), uuid.UUID)
        mock_get_logger.assert_called_once()

        # Trigger a read to generate a log call
        file_path = Path("sample.json")
        file_path.write_text(json.dumps({"a": 1}), encoding="utf-8")
        handler.file_path = file_path  # assign the test file path
        handler.read()

        # Assert the fake_logger captured the log
        fake_logger.info.assert_called_once()
        log_data = fake_logger.info.call_args[0][0]
        assert "success=True" in log_data
        assert str(file_path) in log_data
        assert "elapsed_ms" in log_data
        assert "file_size" in log_data

    def test_init_with_custom_logger(self):
        """Should use custom logger and trace_id if provided."""
        mock_logger = MagicMock()
        trace_id = str(uuid.uuid4())
        handler = JSONFileHandler(file_path="file.json", logger=mock_logger, trace_id=trace_id)

        assert handler.logger == mock_logger
        assert handler.file_path.name == "file.json"
        assert handler.trace_id == trace_id

    # -------------------------
    # Read / Write Tests
    # -------------------------
    def test_read_success(self):
        """Read valid JSON file and assert structured logging."""
        file_path = self.tmp_path / "sample.json"
        file_path.write_text(json.dumps({"name": "Alice", "age": 25}), encoding="utf-8")

        mock_logger = MagicMock()
        handler = JSONFileHandler(file_path, logger=mock_logger, trace_id=None)

        result = handler.read()
        assert result == {"name": "Alice", "age": 25}

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "success=True" in log_data
        assert str(file_path) in log_data
        assert "elapsed_ms" in log_data
        assert "file_size" in log_data
        """
        'JSONFileHandler.read succeeded | trace_id=ba9785e0-f6a5-46c5-ac1d-c27339d28472 file_path=/private/var/folders/cr/_cffpwjj4tj81h6fnjg7008c0000gq/T/pytest-of-jayanth.ns/pytest-22/test_read_success0/sample.json elapsed_ms=3.23 success=True file_size=28'
        """

    def test_read_failure_invalid_json(self):
        """Invalid JSON triggers exception and logs failure."""
        file_path = self.tmp_path / "broken.json"
        file_path.write_text("{invalid-json}", encoding="utf-8")

        mock_logger = MagicMock()
        handler = JSONFileHandler(file_path, logger=mock_logger, trace_id=None)

        import json as std_json

        with pytest.raises(std_json.JSONDecodeError):
            handler.read()

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "success=False" in log_data
        assert "error" in log_data

    def test_write_success(self):
        """Write JSON data and assert structured logging."""
        file_path = self.tmp_path / "output.json"
        mock_logger = MagicMock()
        handler = JSONFileHandler(file_path, logger=mock_logger, trace_id=None)

        data = {"language": "Python", "type": "dynamic"}
        handler.write(data)

        # Validate written content
        with open(file_path, "r", encoding="utf-8") as f:
            assert json.load(f) == data

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "success=True" in log_data
        assert "data_type=dict" in log_data

    def test_write_failure_permission_error(self):
        """Simulate write permission error and assert failure logging."""
        file_path = self.tmp_path / "readonly.json"
        mock_logger = MagicMock()
        handler = JSONFileHandler(file_path, logger=mock_logger, trace_id=None)

        # Patch the open used inside file_handlers module only
        with patch("src.utils.file_handlers.open", side_effect=PermissionError("Access denied")):
            import pytest

            with pytest.raises(PermissionError):
                handler.write({"a": 1})

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "success=False" in log_data
        assert "error" in log_data
