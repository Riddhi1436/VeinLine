from django.core.management.base import BaseCommand
from accounts.services import cleanup_expired_otps


class Command(BaseCommand):
    help = "Clean up expired OTP records older than 24 hours"

    def handle(self, *args, **options):
        deleted_count = cleanup_expired_otps()
        self.stdout.write(
            self.style.SUCCESS(f"Successfully cleaned up {deleted_count} expired OTP records")
        )
