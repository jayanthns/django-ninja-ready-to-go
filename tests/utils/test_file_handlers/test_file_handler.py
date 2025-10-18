import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from utils.file_handlers import (
    CSVFileHandler,
    ExcelFileHandler,
    FileHandlerFactory,
    JSONFileHandler,
    TextFileHandler,
)


@pytest.mark.usefixtures("tmp_path")
class TestFileHandlerFactory:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path):
        """Setup temporary file path."""
        self.tmp_path = tmp_path
        self.mock_logger = MagicMock()
        self.trace_id = str(uuid.uuid4())

    @pytest.mark.parametrize(
        "filename,expected_class",
        [
            ("data.json", JSONFileHandler),
            ("table.csv", CSVFileHandler),
            ("report.xls", ExcelFileHandler),
            ("report.xlsx", ExcelFileHandler),
            ("notes.txt", TextFileHandler),
        ],
    )
    def test_get_handler_supported_extensions(self, filename, expected_class):
        file_path = self.tmp_path / filename
        handler = FileHandlerFactory.get_handler(
            file_path=file_path,
            logger=self.mock_logger,
            trace_id=self.trace_id,
        )
        assert isinstance(handler, expected_class)
        assert handler.file_path == file_path
        assert handler.logger == self.mock_logger
        assert handler.trace_id == self.trace_id

    def test_get_handler_unsupported_extension_raises(self):
        file_path = self.tmp_path / "unsupported.md"
        with pytest.raises(ValueError) as excinfo:
            FileHandlerFactory.get_handler(
                file_path=file_path,
                logger=self.mock_logger,
                trace_id=self.trace_id,
            )
        assert "Unsupported file extension" in str(excinfo.value)
