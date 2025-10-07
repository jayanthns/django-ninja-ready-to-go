from django.conf import settings

DATABASES = {
    "default": {
        "ENGINE": settings.DATABASE_ENGINE,
        "NAME": settings.DATABASE_NAME,
        "USER": settings.DATABASE_USER,
        "PASSWORD": settings.DATABASE_PASSWORD,
        "HOST": settings.DATABASE_HOST,
        "PORT": settings.DATABASE_PORT,
    }
}
