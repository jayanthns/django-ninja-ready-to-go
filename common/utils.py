import datetime
import uuid
from decimal import Decimal
from enum import Enum
from typing import Any

from django.db.models import Model


def normalize_value(value: Any) -> Any:
    """Convert any Python object into a JSON-safe type."""

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    # UUID
    if isinstance(value, uuid.UUID):
        return str(value)

    # Date, time, datetime
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()

    # Decimal
    if isinstance(value, Decimal):
        return float(value)

    # Enum
    if isinstance(value, Enum):
        return value.value

    # Django model instance → use its primary key
    if isinstance(value, Model):
        return str(value.pk)

    # List or tuple
    if isinstance(value, (list, tuple)):
        return [normalize_value(v) for v in value]

    # Dict
    if isinstance(value, dict):
        return {k: normalize_value(v) for k, v in value.items()}

    # Fallback
    return str(value)
