# Django Ninja App Generator Script

This directory contains the `create_ninja_app.sh` script, which automates the creation of Django Ninja apps with a standardized v1 structure.

## Overview

The `create_ninja_app.sh` script generates a complete Django Ninja app with all necessary files, stub code, and best practices built-in. It's designed to save time and ensure consistency across all apps in the project.

## What It Does

When you run `make create-app APP=your_app_name`, the script:

1. **Creates Directory Structure**:
   - `apps/your_app_name/` - App root package
   - `apps/your_app_name/v1/` - Version 1 implementation

2. **Generates Python Packages**:
   - `apps/your_app_name/__init__.py` - Makes app root a Python package
   - `apps/your_app_name/v1/__init__.py` - Makes v1 a Python package

3. **Creates Core Files**:
   - `apps.py` - Django app configuration with proper naming
   - `models.py` - Database models with example stubs
   - `schemas.py` - Pydantic schemas for request/response validation
   - `services.py` - Business logic layer with async CRUD examples
   - `views.py` - API endpoints with a health check route
   - `admin.py` - Django admin configuration stubs

4. **Provides Next Steps**:
   - Instructions to add the app to `INSTALLED_APPS`
   - Router registration code for `main/urls.py`
   - Migration commands

## How It Works

### 1. Input Validation
```bash
if [ -z "$1" ]; then
    echo "Error: App name is required"
    exit 1
fi
```
The script checks if an app name was provided and exits with an error if not.

### 2. Name Conversion
```bash
APP_NAME="$1"
CLASS_NAME=$(echo "$APP_NAME" | awk -F_ '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1' OFS="")
```
- `APP_NAME`: The snake_case name provided by the user (e.g., `my_app`)
- `CLASS_NAME`: Converted to PascalCase for class names (e.g., `MyApp`)

**How the conversion works**:
- `awk -F_` splits the string by underscores
- `toupper(substr($i,1,1))` capitalizes the first character
- `tolower(substr($i,2))` lowercases the rest
- `OFS=""` joins without separators

### 3. File Generation
Each file is created using a heredoc (`cat > file << 'EOF'`):
```bash
cat > "$APP_DIR/models.py" << 'EOF'
from django.db import models
# ... content ...
EOF
```

**Why heredocs?**
- Clean, readable multi-line content
- No need to escape special characters
- Easy to maintain and modify

### 4. Template Variables
The script uses shell variable substitution in specific places:
```bash
cat > "$APP_DIR/apps.py" << EOF
class ${CLASS_NAME}Config(AppConfig):
    name = "apps.${APP_NAME}.v1"
EOF
```
- `EOF` (unquoted) allows variable expansion
- `'EOF'` (quoted) prevents variable expansion

## How to Modify Safely

### Adding New Files

To add a new file to the generated app structure:

```bash
# Add after the existing file creation blocks
cat > "$APP_DIR/your_new_file.py" << 'EOF'
# Your content here
EOF
```

**Important**: Add the file creation BEFORE the final success message.

### Modifying Templates

1. **For static content** (no variables needed):
   ```bash
   cat > "$APP_DIR/file.py" << 'EOF'
   # Use single quotes around EOF
   # Content here
   EOF
   ```

2. **For dynamic content** (with variables):
   ```bash
   cat > "$APP_DIR/file.py" << EOF
   # Use unquoted EOF
   # Variables like ${APP_NAME} will be expanded
   EOF
   ```

### Changing the Directory Structure

To change where apps are created:

```bash
# Current:
APP_DIR="apps/${APP_NAME}/v1"

# To create in a different location:
APP_DIR="my_apps/${APP_NAME}/v1"
```

**Warning**: If you change this, you must also update:
- The `INSTALLED_APPS` instructions in the output
- The router registration instructions
- Any hardcoded paths in the templates

### Adding More Instructions

To add more next steps in the output:

```bash
echo "5. Your new instruction here:"
echo "   Details about what to do"
echo ""
```

Add these BEFORE the final empty `echo ""` at the end of the script.

## Common Modifications

### 1. Add a Different File Structure

If you want to add a `tests.py` file:

```bash
# Add after views.py creation
cat > "$APP_DIR/tests.py" << 'EOF'
from django.test import TestCase

# Create your tests here.
EOF
```

### 2. Change the Default Model Template

Edit the models.py heredoc section:

```bash
cat > "$APP_DIR/models.py" << 'EOF'
from django.db import models

# Your custom default model template
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
EOF
```

### 3. Add Custom Imports

To add project-specific imports to generated files:

```bash
cat > "$APP_DIR/views.py" << 'EOF'
from typing import Any, Dict

from ninja import Router

# Add your custom imports
from common.base_schemas import create_api_response_schema
from utils.decorators import require_auth

router = Router()
# ... rest of content
EOF
```

### 4. Customize the Health Check Endpoint

Edit the views.py template to change the health check:

```bash
@router.get("/health/", response=Dict[str, str])
async def health_check(request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": "${APP_NAME}",
        "version": "v1"  # Add version info
    }
```

## FAQ

### Q: Why use `awk` for PascalCase conversion instead of `sed`?
**A**: The `sed` approach with regex didn't work consistently across macOS and Linux. The `awk` solution is more portable and reliable.

### Q: Can I change the version from v1 to something else?
**A**: Yes, but you'll need to:
1. Change `APP_DIR="apps/${APP_NAME}/v1"` to your version
2. Update the `apps.py` template's `name` field
3. Update all instructions in the output messages

### Q: Why are there two `__init__.py` files?
**A**: Python requires `__init__.py` in every directory that should be treated as a package:
- `apps/your_app/` needs one to be importable
- `apps/your_app/v1/` needs one to be importable
This allows imports like `from apps.your_app.v1.models import YourModel`

### Q: Can I add environment-specific configurations?
**A**: Yes! You can add conditional logic:
```bash
if [ "$ENV" = "production" ]; then
    # Add production-specific files
else
    # Add development-specific files
fi
```

### Q: How do I add a README to each generated app?
**A**: Add this after the other file creations:
```bash
cat > "apps/${APP_NAME}/README.md" << EOF
# ${CLASS_NAME} App

Description of the ${APP_NAME} app.

## Endpoints
- \`GET /${APP_NAME}/health/\` - Health check

## Models
- TODO: Document your models

## Setup
1. Add to INSTALLED_APPS
2. Run migrations
3. Register router
EOF
```

### Q: What if I want to use a different router pattern?
**A**: Edit the views.py template section and change the router initialization and endpoint patterns to match your preferred style.

### Q: Can I make the script interactive?
**A**: Yes! Add prompts:
```bash
read -p "Enter app description: " APP_DESCRIPTION
read -p "Add authentication? (y/n): " ADD_AUTH

if [ "$ADD_AUTH" = "y" ]; then
    # Add auth-related code to templates
fi
```

### Q: How do I test my changes to the script?
**A**: 
1. Make your changes to `create_ninja_app.sh`
2. Run: `make create-app APP=test_app`
3. Verify the generated files in `apps/test_app/`
4. Delete the test app: `rm -rf apps/test_app`
5. Repeat until satisfied

### Q: What's the best way to add custom business logic templates?
**A**: Modify the `services.py` heredoc to include your common patterns:
```bash
cat > "$APP_DIR/services.py" << 'EOF'
from typing import List, Optional
from common.base_service import BaseService  # Your custom base

class YourModelService(BaseService):
    # Your standard CRUD methods
    pass
EOF
```

## Troubleshooting

### Script fails with "command not found"
- Ensure the script has execute permissions: `chmod +x scripts/create_ninja_app.sh`
- Check that bash is available: `which bash`

### PascalCase conversion produces wrong output
- Test the conversion separately: `echo "my_app" | awk -F_ '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1' OFS=""`
- Expected: `MyApp`

### Generated files have wrong indentation
- Ensure heredocs don't have leading tabs/spaces
- The content between `<< 'EOF'` and `EOF` should be flush left

### Variables not expanding in templates
- Check if you're using `<< 'EOF'` (quoted) vs `<< EOF` (unquoted)
- Quoted prevents expansion, unquoted allows it

## Best Practices

1. **Always test changes** with a test app before committing
2. **Keep templates minimal** - users can customize after generation
3. **Document any custom additions** in this README
4. **Use consistent formatting** across all generated files
5. **Provide clear next steps** in the output
6. **Make the script idempotent** - running it twice shouldn't break things
7. **Add validation** for app names (e.g., no spaces, special characters)

## Contributing

When modifying this script:
1. Test thoroughly with different app names
2. Update this README with your changes
3. Update the main project README if the usage changes
4. Consider backward compatibility

## Related Files

- `Makefile` - Contains the `create-app` target that calls this script
- `README.md` - Main project documentation with usage examples
- `apps/animals_app/` - Example app structure to reference
