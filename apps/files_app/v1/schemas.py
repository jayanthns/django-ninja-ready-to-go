from typing import Any, Dict, List

from ninja import Schema


class FileSuccessSchema(Schema):
    message: str
    filename: str
    size: int
    human_readable_size: str


class LinearDataResponseSchema(Schema):
    message: str
    filename: str
    total_rows: int
    preview_rows: List[Dict[str, Any]]
