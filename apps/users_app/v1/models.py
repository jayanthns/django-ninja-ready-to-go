from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from common.models import BaseModel


class User(BaseModel):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Store hashed passwords

    async def set_password(self, raw_password: str):
        """Asynchronously hash the password before saving."""
        self.password = await sync_to_async(make_password)(raw_password)

    async def check_password(self, raw_password: str) -> bool:
        """Asynchronously check if the given password matches the stored hash."""
        return await sync_to_async(check_password)(raw_password, self.password)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email  # pragma: no cover
