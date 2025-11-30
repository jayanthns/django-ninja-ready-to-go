from django.db import models

from common.models import BaseModel


class Animal(BaseModel):
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    age = models.IntegerField()

    def __str__(self) -> str:
        return self.name
