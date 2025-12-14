from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from apps.ping_app.v1.services.cache_health_services import CacheHealthService


class Command(BaseCommand):
    help = "Check Redis health"

    def handle(self, *args, **kwargs):
        self.stdout.write("Checking Redis health...")
        try:
            # Run the async health check synchronously
            health_status = async_to_sync(CacheHealthService.check_cache_health)()

            if health_status.is_healthy:
                self.stdout.write(self.style.SUCCESS("✅ Redis is HEALTHY"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Redis is UNHEALTHY: {health_status.error_message}"))
                exit(1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Redis health check failed with exception: {str(e)}"))
            exit(1)
