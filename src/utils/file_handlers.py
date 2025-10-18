import csv
import json
import time
import uuid
from abc import ABC, abstractmethod
from logging import LoggerAdapter
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from common.logger_helper import get_logger_with_trace


class BaseFileHandler(ABC):
    """
    Abstract base class defining interface for file operations.
    Provides logging, tracing, and read/write abstractions.
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        logger: Optional[LoggerAdapter] = None,
        trace_id: Optional[uuid.UUID] = None,
    ):
        self.file_path = Path(file_path)
        self.trace_id = str(trace_id or uuid.uuid4())
        self.logger = logger or get_logger_with_trace(trace_id=self.trace_id, logger_name=__name__)

    @abstractmethod
    def read(self) -> Any:
        """Read file content and return parsed data."""
        raise NotImplementedError

    @abstractmethod
    def write(self, data: Any) -> None:
        """Write data into the file."""
        raise NotImplementedError

    # ---------- Helper ----------
    def _log_operation(self, operation: str, start_time: float, success: bool, extra: Optional[dict] = None):
        """Helper for structured logging of read/write operations (compact inline style)."""
        elapsed = round((time.time() - start_time) * 1000, 2)
        msg = f"{self.__class__.__name__}.{operation} {'succeeded' if success else 'failed'}"

        # Prepare extra dict
        full_extra = {
            "trace_id": getattr(self, "trace_id", "no-trace-id"),
            "file_path": str(self.file_path),
            "elapsed_ms": elapsed,
            "success": success,
            **(extra or {}),
        }

        # Convert to compact string representation
        extra_str = " ".join(f"{k}={v}" for k, v in full_extra.items())

        # Log it inline
        self.logger.info(f"{msg} | {extra_str}")


# ----------------------- JSON -----------------------
class JSONFileHandler(BaseFileHandler):
    def read(self) -> dict | list:
        start = time.time()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._log_operation("read", start, True, {"file_size": self.file_path.stat().st_size})
            return data
        except Exception as e:
            self._log_operation("read", start, False, {"error": str(e)})
            raise

    def write(self, data: dict | list) -> None:
        start = time.time()
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self._log_operation("write", start, True, {"data_type": type(data).__name__})
        except Exception as e:
            self._log_operation("write", start, False, {"error": str(e)})
            raise


# ----------------------- CSV -----------------------
class CSVFileHandler(BaseFileHandler):
    def read(self) -> List[Dict[str, Any]]:
        start = time.time()
        try:
            with open(self.file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = [row for row in reader]
            self._log_operation("read", start, True, {"rows": len(data)})
            return data
        except Exception as e:
            self._log_operation("read", start, False, {"error": str(e)})
            raise

    def write(self, data: List[Dict[str, Any]]) -> None:
        start = time.time()
        try:
            if not data:
                raise ValueError("No data to write to CSV")

            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            self._log_operation("write", start, True, {"rows": len(data)})
        except Exception as e:
            self._log_operation("write", start, False, {"error": str(e)})
            raise


# ----------------------- Excel -----------------------
class ExcelFileHandler(BaseFileHandler):
    def read(self, sheet_name: Union[str, int, None] = 0) -> pd.DataFrame:
        start = time.time()
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            self._log_operation("read", start, True, {"rows": len(df), "columns": len(df.keys())})
            return df
        except Exception as e:
            self._log_operation("read", start, False, {"error": str(e)})
            raise

    def write(self, data: pd.DataFrame, sheet_name: str = "Sheet1") -> None:
        start = time.time()
        try:
            if not isinstance(data, pd.DataFrame):
                raise TypeError("Data must be a pandas DataFrame for Excel writing.")
            data.to_excel(self.file_path, sheet_name=sheet_name, index=False)
            self._log_operation("write", start, True, {"rows": len(data), "columns": len(data.columns)})
        except Exception as e:
            self._log_operation("write", start, False, {"error": str(e)})
            raise

    # Convenience methods remain unchanged
    def read_as_dicts(self, sheet_name: Union[str, int, None] = 0) -> List[Dict[str, Any]]:
        return self.read(sheet_name).to_dict(orient="records")

    def read_as_json(self, sheet_name: Union[str, int, None] = 0) -> str:
        return self.read(sheet_name).to_json(orient="records", indent=4)

    def read_as_columns(self, sheet_name: Union[str, int, None] = 0) -> Dict[str, List[Any]]:
        return self.read(sheet_name).to_dict(orient="list")


# ----------------------- Text -----------------------
class TextFileHandler(BaseFileHandler):
    def read(self) -> str:
        start = time.time()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self._log_operation("read", start, True, {"file_size": self.file_path.stat().st_size})
            return content
        except Exception as e:
            self._log_operation("read", start, False, {"error": str(e)})
            raise

    def write(self, data: str) -> None:
        start = time.time()
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(data)
            self._log_operation("write", start, True, {"chars": len(data)})
        except Exception as e:
            self._log_operation("write", start, False, {"error": str(e)})
            raise


# ----------------------- Factory -----------------------
class FileHandlerFactory:
    handlers_map = {
        ".json": JSONFileHandler,
        ".csv": CSVFileHandler,
        ".xls": ExcelFileHandler,
        ".xlsx": ExcelFileHandler,
        ".txt": TextFileHandler,
    }

    @classmethod
    def get_handler(
        cls, file_path: Union[str, Path], logger: Optional[LoggerAdapter], trace_id: Optional[uuid.UUID]
    ) -> BaseFileHandler:
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        handler_class = cls.handlers_map.get(ext)
        if not handler_class:
            raise ValueError(f"Unsupported file extension: {ext}")
        return handler_class(file_path, logger=logger, trace_id=trace_id)
