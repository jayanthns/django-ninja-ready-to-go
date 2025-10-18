import csv
import json
import uuid
from abc import ABC, abstractmethod
from logging import LoggerAdapter
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from src.common.logger_helper import get_logger_with_trace


class BaseFileHandler(ABC):
    """
    Abstract base class defining interface for file operations.
    Enforces read() and write() methods for all subclasses.
    """

    def __init__(
        self, file_path: Union[str, Path], logger: Optional[LoggerAdapter], trace_id: Optional[uuid.UUID4]
    ):
        self.file_path = Path(file_path)
        self.trace_id = trace_id or str(uuid.uuid4())
        self.logger = logger if logger else get_logger_with_trace()

    @abstractmethod
    def read(self) -> Any:
        """Read file content and return parsed data."""
        pass

    @abstractmethod
    def write(self, data: Any) -> None:
        """Write data into the file."""
        pass


# ----------------------- JSON -----------------------
class JSONFileHandler(BaseFileHandler):
    def read(self) -> dict | list:
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, data: dict | list) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


# ----------------------- CSV -----------------------
class CSVFileHandler(BaseFileHandler):
    def read(self) -> List[Dict[str, Any]]:
        with open(self.file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]

    def write(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            raise ValueError("No data to write to CSV")

        with open(self.file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


# ----------------------- Excel -----------------------
class ExcelFileHandler(BaseFileHandler):
    def read(self, sheet_name: Union[str, int, None] = None) -> pd.DataFrame:
        return pd.read_excel(self.file_path, sheet_name=sheet_name)

    def write(self, data: pd.DataFrame, sheet_name: str = "Sheet1") -> None:
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Data must be a pandas DataFrame for Excel writing.")
        data.to_excel(self.file_path, sheet_name=sheet_name, index=False)

    # ---------- Convenience Conversions ----------
    def read_as_dicts(self, sheet_name: Union[str, int, None] = None) -> List[Dict[str, Any]]:
        """Return Excel data as list of dictionaries (records)."""
        df = self.read(sheet_name)
        return df.to_dict(orient="records")

    def read_as_json(self, sheet_name: Union[str, int, None] = None) -> str:
        """Return Excel data as JSON string."""
        df = self.read(sheet_name)
        return df.to_json(orient="records", indent=4)

    def read_as_columns(self, sheet_name: Union[str, int, None] = None) -> Dict[str, List[Any]]:
        """Return Excel data as dict of columns."""
        df = self.read(sheet_name)
        return df.to_dict(orient="list")


# ----------------------- Text -----------------------
class TextFileHandler(BaseFileHandler):
    def read(self) -> str:
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()

    def write(self, data: str) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(data)


# ----------------------- Factory -----------------------
class FileHandlerFactory:
    """
    Factory class to get the appropriate handler based on file extension.
    """

    handlers_map = {
        ".json": JSONFileHandler,
        ".csv": CSVFileHandler,
        ".xls": ExcelFileHandler,
        ".xlsx": ExcelFileHandler,
        ".txt": TextFileHandler,
    }

    @classmethod
    def get_handler(cls, file_path: Union[str, Path]) -> BaseFileHandler:
        file_path = Path(file_path)
        ext = file_path.suffix.lower()

        handler_class = cls.handlers_map.get(ext)
        if not handler_class:
            raise ValueError(f"Unsupported file extension: {ext}")

        return handler_class(file_path)
