from typing import List, Optional

from .models import Animal
from .schemas import AnimalCreateSchema


class AnimalService:
    @staticmethod
    async def create_animal(name: str, species: str, age: int) -> Animal:
        """Create a new animal asynchronously."""
        return await Animal.objects.acreate(name=name, species=species, age=age)

    @staticmethod
    async def list_animals() -> List[Animal]:
        """Retrieve all animals asynchronously."""
        return [animal async for animal in Animal.objects.all()]

    @staticmethod
    async def get_animal(animal_id: int) -> Optional[Animal]:
        """Retrieve a single animal by ID asynchronously."""
        return await Animal.objects.filter(id=animal_id).afirst()

    @staticmethod
    async def update_animal(animal_id: int, data: AnimalCreateSchema) -> Optional[Animal]:
        """Update an animal asynchronously."""
        updated_count = await Animal.objects.filter(id=animal_id).aupdate(**data.dict())
        if updated_count:
            return await Animal.objects.aget(id=animal_id)
        return None

    @staticmethod
    async def delete_animal(animal_id: int) -> bool:
        """Delete an animal asynchronously."""
        deleted_count, _ = await Animal.objects.filter(id=animal_id).adelete()
        return deleted_count > 0
