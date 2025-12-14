from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from apps.ping_app.v1.services.database_health_services import DatabaseHealthService


class Command(BaseCommand):
    help = "Check database health"

    def handle(self, *args, **kwargs):
        self.stdout.write("Checking Database health...")
        try:
            # Run the async health check synchronously
            health_status = async_to_sync(DatabaseHealthService.check_database_health)()

            if health_status.is_healthy:
                self.stdout.write(self.style.SUCCESS("✅ Database is HEALTHY"))
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Database is UNHEALTHY: {health_status.error_message}")
                )
                exit(1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Database health check failed with exception: {str(e)}"))
            exit(1)
