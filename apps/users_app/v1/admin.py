from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "created_at", "updated_at")
    search_fields = ("username", "email")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
