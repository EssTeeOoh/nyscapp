# management/commands/clear_expired_notifications.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from nysc.models import Notification
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Clears notifications older than 24 hours if marked as read.'

    def handle(self, *args, **options):
        now = timezone.now()
        for user in User.objects.all():
            expired_notifications = user.notifications.filter(
                is_read=True,
                created_at__lt=now - datetime.timedelta(hours=24)
            )
            if expired_notifications.exists():
                count = expired_notifications.delete()[0]
                self.stdout.write(self.style.SUCCESS(f"Cleared {count} expired notifications for {user.username}"))