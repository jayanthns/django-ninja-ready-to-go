#!/bin/bash

# Script to create a new Django Ninja app with v1 structure
# Usage: ./create_ninja_app.sh app_name

set -e

if [ -z "$1" ]; then
    echo "Error: App name is required"
    echo "Usage: make create-app APP=your_app_name"
    exit 1
fi

APP_NAME="$1"
APP_DIR="apps/${APP_NAME}/v1"

# Convert app_name to PascalCase for class names
# e.g., my_app -> MyApp, user_profile -> UserProfile
CLASS_NAME=$(echo "$APP_NAME" | awk -F_ '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1' OFS="")

echo "Creating Django Ninja app: $APP_NAME"
echo "Directory: $APP_DIR"
echo "Class name: $CLASS_NAME"

# Create directory structure
mkdir -p "$APP_DIR"

# Create __init__.py in app root (apps/app_name/)
cat > "apps/${APP_NAME}/__init__.py" << 'EOF'
"""
Django Ninja app package.
"""
EOF

# Create __init__.py in v1 directory
cat > "$APP_DIR/__init__.py" << 'EOF'
"""
Django Ninja app with async support.
"""
EOF

# Create apps.py
cat > "$APP_DIR/apps.py" << EOF
from django.apps import AppConfig


class ${CLASS_NAME}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.${APP_NAME}.v1"
    label = "apps_${APP_NAME}_v1"
EOF

# Create models.py
cat > "$APP_DIR/models.py" << 'EOF'
from common.models import BaseModel


# Example model - customize as needed
# class YourModel(BaseModel):
#     name = models.CharField(max_length=100)
#
#     def __str__(self) -> str:
#         return self.name
#
#     class Meta:
#         verbose_name = "Your Model"
#         verbose_name_plural = "Your Models"
#         ordering = ["-created_at"]
EOF

# Create schemas.py
cat > "$APP_DIR/schemas.py" << 'EOF'
import uuid
from typing import Optional

from ninja import Schema


# Example schemas - customize as needed
# class YourModelSchema(Schema):
#     id: uuid.UUID
#     name: str
#     created_at: str
#
#
# class YourModelCreateSchema(Schema):
#     name: str
#
#
# class YourModelResponseSchema(Schema):
#     data: Optional[YourModelSchema] = None
#     error: Optional[dict] = None
#     trace_id: uuid.UUID
#
#     class Config:
#         arbitrary_types_allowed = True
EOF

# Create services.py
cat > "$APP_DIR/services.py" << 'EOF'
from typing import List, Optional


# Example service class - customize as needed
# class YourModelService:
#     @staticmethod
#     async def create(name: str):
#         """Create a new instance asynchronously."""
#         from .models import YourModel
#         return await YourModel.objects.acreate(name=name)
#
#     @staticmethod
#     async def list_all() -> List:
#         """Retrieve all instances asynchronously."""
#         from .models import YourModel
#         return [item async for item in YourModel.objects.all()]
#
#     @staticmethod
#     async def get_by_id(item_id: int) -> Optional:
#         """Retrieve a single instance by ID asynchronously."""
#         from .models import YourModel
#         return await YourModel.objects.filter(id=item_id).afirst()
#
#     @staticmethod
#     async def update(item_id: int, **kwargs) -> Optional:
#         """Update an instance asynchronously."""
#         from .models import YourModel
#         updated_count = await YourModel.objects.filter(id=item_id).aupdate(**kwargs)
#         if updated_count:
#             return await YourModel.objects.aget(id=item_id)
#         return None
#
#     @staticmethod
#     async def delete(item_id: int) -> bool:
#         """Delete an instance asynchronously."""
#         from .models import YourModel
#         deleted_count, _ = await YourModel.objects.filter(id=item_id).adelete()
#         return deleted_count > 0
EOF

# Create views.py
cat > "$APP_DIR/views.py" << 'EOF'
from typing import Any, Dict

from ninja import Router

# from common.base_schemas import create_api_response_schema
# from .schemas import YourModelSchema, YourModelCreateSchema
# from .services import YourModelService

router = Router()


# Example endpoints - uncomment and customize as needed
# @router.post("/", response=create_api_response_schema(YourModelSchema))
# async def create_item(request, payload: YourModelCreateSchema):
#     """Create a new item (Async)."""
#     request.logger.info(f"Creating new item: {payload.name}")
#
#     try:
#         item = await YourModelService.create(payload.name)
#         request.logger.info(f"Successfully created item with ID: {item.id}")
#
#         return {
#             "data": item,
#             "trace_id": str(request.trace_id),
#             "error": {},
#         }
#     except Exception as e:
#         request.logger.exception(f"Failed to create item")
#         raise
#
#
# @router.get("/", response=create_api_response_schema(List[YourModelSchema]))
# async def list_items(request):
#     """Retrieve all items (Async)."""
#     return {
#         "data": await YourModelService.list_all(),
#         "trace_id": str(request.trace_id),
#         "error": {}
#     }
#
#
# @router.get("/{item_id}/", response={200: YourModelSchema, 404: Dict[str, Any]})
# async def get_item(request, item_id: int):
#     """Retrieve a single item by ID (Async)."""
#     item = await YourModelService.get_by_id(item_id)
#     if not item:
#         return 404, {"error": "Item not found"}
#     return item


@router.get("/health/", response=Dict[str, str])
async def health_check(request):
    """Health check endpoint."""
    return {"status": "healthy", "app": "${APP_NAME}"}
EOF

# Create admin.py
cat > "$APP_DIR/admin.py" << 'EOF'
from django.contrib import admin

# Register your models here.
# Example:
# from .models import YourModel
#
# @admin.register(YourModel)
# class YourModelAdmin(admin.ModelAdmin):
#     list_display = ('name', 'created_at', 'updated_at')
#     search_fields = ('name',)
#     list_filter = ('created_at',)
#     readonly_fields = ('created_at', 'updated_at')
EOF

echo ""
echo "✅ App created successfully!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Add the app to INSTALLED_APPS in main/settings/base.py:"
echo "   INSTALLED_APPS = ["
echo "       # ... other apps"
echo "       \"apps.${APP_NAME}.v1\","
echo "   ]"
echo ""
echo "2. Register the router in main/urls.py:"
echo "   from apps.${APP_NAME}.v1.views import router as ${APP_NAME}_router"
echo "   api.add_router(\"/${APP_NAME}/\", ${APP_NAME}_router, tags=[\"${CLASS_NAME}\"])"
echo ""
echo "3. Create and run migrations:"
echo "   make makemigrations"
echo "   make migrate"
echo ""
echo "4. Customize the generated files in: $APP_DIR"
echo "   - models.py: Define your database models"
echo "   - schemas.py: Define Pydantic schemas for validation"
echo "   - services.py: Implement business logic"
echo "   - views.py: Create API endpoints"
echo "   - admin.py: Configure Django admin (optional)"
echo ""
