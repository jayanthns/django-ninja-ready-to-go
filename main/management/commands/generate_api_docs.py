import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from main.urls import api


class Command(BaseCommand):
    help = "Generate OpenAPI schema, Swagger UI, and ReDoc documentation files."

    def handle(self, *args, **options):
        docs_dir = settings.ROOT_DIR / "docs"
        os.makedirs(docs_dir, exist_ok=True)

        # Generate OpenAPI JSON
        schema = api.get_openapi_schema()
        openapi_path = docs_dir / "openapi.json"
        with open(openapi_path, "w") as f:
            json.dump(schema, f, indent=4)
        self.stdout.write(self.style.SUCCESS(f"Successfully generated OpenAPI schema at {openapi_path}"))

        # Generate Swagger UI HTML
        swagger_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>SwaggerUI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js" crossorigin></script>
<script>
    window.onload = () => {
        window.ui = SwaggerUIBundle({
            url: './openapi.json',
            dom_id: '#swagger-ui',
        });
    };
</script>
</body>
</html>
"""
        swagger_path = docs_dir / "swagger.html"
        with open(swagger_path, "w") as f:
            f.write(swagger_html)
        self.stdout.write(self.style.SUCCESS(f"Successfully generated Swagger UI at {swagger_path}"))

        # Generate ReDoc HTML
        redoc_html = """<!DOCTYPE html>
<html>
<head>
    <title>ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
<div id="redoc-container"></div>
<script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0-rc.55/bundles/redoc.standalone.js"> </script>
<script>
    Redoc.init('./openapi.json', {}, document.getElementById('redoc-container'))
</script>
</body>
</html>
"""
        redoc_path = docs_dir / "redoc.html"
        with open(redoc_path, "w") as f:
            f.write(redoc_html)
        self.stdout.write(self.style.SUCCESS(f"Successfully generated ReDoc at {redoc_path}"))
