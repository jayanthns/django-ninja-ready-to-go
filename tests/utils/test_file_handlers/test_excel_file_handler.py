import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils.file_handlers import ExcelFileHandler  # adjust import to your path


@pytest.mark.usefixtures("tmp_path")
class TestExcelFileHandler:
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

        handler = ExcelFileHandler(file_path="sample.xlsx", logger=None, trace_id=None)

        assert handler.logger == fake_logger
        assert isinstance(uuid.UUID(handler.trace_id), uuid.UUID)
        mock_get_logger.assert_called_once()

    def test_init_with_custom_logger(self):
        mock_logger = MagicMock()
        trace_id = str(uuid.uuid4())
        handler = ExcelFileHandler(file_path="file.xlsx", logger=mock_logger, trace_id=trace_id)

        assert handler.logger == mock_logger
        assert handler.file_path.name == "file.xlsx"
        assert handler.trace_id == trace_id

    # -------------------------
    # Read / Write Tests
    # -------------------------
    def test_write_and_read_success(self):
        """Write a DataFrame and read it back, check logging."""
        file_path = self.tmp_path / "test.xlsx"
        mock_logger = MagicMock()
        handler = ExcelFileHandler(file_path, logger=mock_logger, trace_id=None)

        data = pd.DataFrame([{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}])

        # Write Excel
        handler.write(data)

        # Validate written content
        read_df = pd.read_excel(file_path)
        pd.testing.assert_frame_equal(read_df, data)

        # Logging assertions for write
        mock_logger.info.assert_called()
        log_data = mock_logger.info.call_args[0][0]
        assert "ExcelFileHandler.write succeeded" in log_data
        assert "rows=2" in log_data
        assert "columns=2" in log_data
        assert str(file_path) in log_data
        assert "elapsed_ms" in log_data
        assert "success=True" in log_data

        # Reset mock for read logging
        mock_logger.reset_mock()

        # Read Excel
        read_data = handler.read()
        pd.testing.assert_frame_equal(read_data, data)

        # Logging assertions for read
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "ExcelFileHandler.read succeeded" in log_data
        assert "rows=2" in log_data
        assert "columns=2" in log_data
        assert str(file_path) in log_data
        assert "elapsed_ms" in log_data
        assert "success=True" in log_data

    def test_read_failure_file_missing(self):
        """Reading non-existent file should raise FileNotFoundError and log failure."""
        file_path = self.tmp_path / "missing.xlsx"
        mock_logger = MagicMock()
        handler = ExcelFileHandler(file_path, logger=mock_logger, trace_id=None)

        with pytest.raises(FileNotFoundError):
            handler.read()

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "ExcelFileHandler.read failed" in log_data
        assert "FileNotFoundError" in log_data or "No such file" in log_data
        assert "success=False" in log_data

    def test_write_failure_type_error(self):
        """Writing non-DataFrame should raise TypeError and log failure."""
        file_path = self.tmp_path / "wrong_type.xlsx"
        mock_logger = MagicMock()
        handler = ExcelFileHandler(file_path, logger=mock_logger, trace_id=None)

        with pytest.raises(TypeError):
            handler.write([{"name": "Alice"}])  # not a DataFrame

        # Logging assertions
        mock_logger.info.assert_called_once()
        log_data = mock_logger.info.call_args[0][0]
        assert "ExcelFileHandler.write failed" in log_data
        assert "Data must be a pandas DataFrame" in log_data
        assert "success=False" in log_data

    def test_read_as_dicts_and_json(self):
        """Test convenience methods read_as_dicts and read_as_json."""
        file_path = self.tmp_path / "data.xlsx"
        mock_logger = MagicMock()
        handler = ExcelFileHandler(file_path, logger=mock_logger, trace_id=None)

        data = pd.DataFrame([{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}])
        handler.write(data)

        # read_as_dicts
        dicts = handler.read_as_dicts()
        assert dicts == [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]

        # read_as_json
        json_str = handler.read_as_json()
        import json

        parsed = json.loads(json_str)
        assert parsed == [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]

    def test_read_as_columns(self):
        """Test read_as_columns method."""
        file_path = self.tmp_path / "columns.xlsx"
        mock_logger = MagicMock()
        handler = ExcelFileHandler(file_path, logger=mock_logger, trace_id=None)

        data = pd.DataFrame([{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}])
        handler.write(data)

        columns = handler.read_as_columns()
        assert columns == {"name": ["Alice", "Bob"], "age": [25, 30]}
