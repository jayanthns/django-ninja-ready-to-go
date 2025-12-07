from django.contrib import admin

from .models import Animal


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "age", "created_at", "updated_at")
    search_fields = ("name", "species")
    list_filter = ("species", "created_at")
