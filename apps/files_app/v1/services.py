import csv
import io
import json
from typing import Any, Dict, Generator, List

from django.core.files.uploadedfile import UploadedFile
from ninja.errors import HttpError


class FileService:
    @staticmethod
    def validate_file_size(file: UploadedFile, limit_kb: int = 25) -> None:
        """
        Validates that the file size is within the specified limit (in KB).
        """
        if file.size > limit_kb * 1024:
            raise HttpError(
                400, f"File size exceeds the limit of {limit_kb}KB. Current size: {file.size / 1024:.2f}KB"
            )

    @staticmethod
    def parse_linear_file(file: UploadedFile) -> List[Dict[str, Any]]:
        """
        Parses a linear data file (CSV or JSON) and returns a list of records.
        Returns the top 10 records.
        """
        # Ensure we are at the start of the file
        file.seek(0)
        content = file.read().decode("utf-8")
        file_ext = file.name.split(".")[-1].lower()

        data = []

        if file_ext == "csv":
            # Parse CSV
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)
            data = [row for row in reader]
        elif file_ext == "json":
            # Parse JSON
            try:
                json_data = json.loads(content)
                if isinstance(json_data, list):
                    data = json_data
                else:
                    raise HttpError(400, "JSON file must contain a list of objects.")
            except json.JSONDecodeError:
                raise HttpError(400, "Invalid JSON file.")
        else:
            raise HttpError(400, "Unsupported file type. Only .csv and .json are allowed for linear data.")

        return data[:10]

    @staticmethod
    def get_dummy_content(size_kb: int = 25) -> str:
        """
        Generates dummy text content of a specific size.
        """
        # Generate a string of approximately size_kb KB
        # 1 KB = 1024 bytes
        # We'll use a simple repeated pattern
        pattern = "This is a line of dummy content for the file reference app.\n"
        pattern_size = len(pattern.encode("utf-8"))
        repeats = (size_kb * 1024) // pattern_size
        return pattern * repeats

    @staticmethod
    def get_file_stream(filename: str, size_kb: int = 25) -> Generator[str, None, None]:
        """
        Yields chunks of data to simulate file streaming.
        """
        content = FileService.get_dummy_content(size_kb)
        chunk_size = 1024  # 1KB chunks

        # Simulate reading in chunks
        for i in range(0, len(content), chunk_size):
            yield content[i : i + chunk_size]

    @staticmethod
    def get_file_content(filename: str, size_kb: int = 25) -> str:
        """
        Returns the full content of a dummy file.
        """
        return FileService.get_dummy_content(size_kb)
