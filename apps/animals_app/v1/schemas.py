import uuid
from typing import Optional

from ninja import Schema


class AnimalSchema(Schema):
    id: int
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

    class Config:
        arbitrary_types_allowed = True  # ✅ Needed if using custom types
