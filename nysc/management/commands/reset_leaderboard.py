# nysc/management/commands/reset_leaderboard.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from nysc.models import LeaderboardEntry, LeaderboardReset, Notification
from django.utils import timezone
import logging
import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Resets the leaderboard every Sunday at midnight and updates PPA counts. Use --force to reset immediately.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force reset the leaderboard immediately.')

    def handle(self, *args, **options):
        try:
            now = timezone.now()
            reset, created = LeaderboardReset.objects.get_or_create(id=1)
            last_reset = reset.last_reset

            # Update PPA counts only if not forcing a reset
            if not options['force']:
                for entry in LeaderboardEntry.objects.all():
                    old_total_ppas = entry.total_ppas
                    old_verified_ppas = entry.verified_ppas
                    new_total_ppas = entry.user.ppas.count()
                    new_verified_ppas = entry.user.ppas.filter(verification_status=True).count()  # Assuming verification_status is a boolean
                    if old_total_ppas != new_total_ppas or old_verified_ppas != new_verified_ppas:
                        entry.total_ppas = new_total_ppas
                        entry.verified_ppas = new_verified_ppas
                        entry.points = (new_total_ppas * 10) + (new_verified_ppas * 20)
                        entry.save()
                        logger.info(f"Updated {entry.user.username}: Total PPAs {old_total_ppas} -> {new_total_ppas}, Verified PPAs {old_verified_ppas} -> {new_verified_ppas}")
                    else:
                        logger.debug(f"No change for {entry.user.username}: Total PPAs {new_total_ppas}, Verified PPAs {new_verified_ppas}")

            # Perform reset if condition or force is met
            should_reset = options['force'] or (not last_reset or (now.weekday() == 6 and now.hour == 0 and now.minute == 0 and last_reset < now - datetime.timedelta(days=7)))
            if should_reset:
                for entry in LeaderboardEntry.objects.all():  # Loop to handle multiple entries and log
                    old_total_ppas = entry.total_ppas
                    entry.total_ppas = 0
                    entry.verified_ppas = 0
                    entry.points = 0
                    entry.save()
                    logger.info(f"Reset {entry.user.username}: Total PPAs {old_total_ppas} -> 0, Verified PPAs {entry.verified_ppas} -> 0")
                reset.last_reset = now
                reset.save()
                logger.info(f"Leaderboard reset at {now} for all users")

                # Notify all users
                users = User.objects.all()
                for user in users:
                    Notification.objects.create(
                        user=user,
                        message="Leaderboard has been reset! Start earning points with new PPAs!",
                        type='leaderboard',
                        is_read=False
                    )
                logger.info(f"Notifications sent to {users.count()} users")
                self.stdout.write(self.style.SUCCESS('Leaderboard reset successfully'))
            else:
                logger.debug(f"No reset needed at {now}. Last reset: {last_reset}")
                self.stdout.write(self.style.SUCCESS('Leaderboard updated with current PPA counts'))
        except Exception as e:
            logger.error(f"Error during leaderboard update/reset: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'Failed to update/reset leaderboard: {str(e)}'))