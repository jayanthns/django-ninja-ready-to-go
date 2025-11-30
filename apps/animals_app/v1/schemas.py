import uuid
from typing import Optional

from ninja import Schema
from pydantic import ConfigDict


class AnimalSchema(Schema):
    id: uuid.UUID
    name: str
    species: str
    age: int


class AnimalCreateSchema(Schema):
    name: str
    species: str
    age: int


class AnimalResponseSchema(Schema):
    data: Optional[AnimalSchema] = None  # ✅ Correct data field
    error: Optional[dict] = None  # ✅ Default as None (avoid mutable defaults)
    trace_id: uuid.UUID  # ✅ Proper UUID type (Swagger will show as UUID)

    model_config = ConfigDict(arbitrary_types_allowed=True)
