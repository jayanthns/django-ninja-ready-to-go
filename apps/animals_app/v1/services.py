from common.services import BaseCRUDService

from .models import Animal


class AnimalService(BaseCRUDService):
    model = Animal
