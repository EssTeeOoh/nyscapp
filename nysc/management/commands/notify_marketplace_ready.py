from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from nysc.models import MarketplaceSubscription
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Notifies all subscribed users that the marketplace is ready.'

    def handle(self, *args, **options):
        subscriptions = MarketplaceSubscription.objects.filter(notified=False)
        if not subscriptions.exists():
            self.stdout.write(self.style.WARNING('No unsubscribed users to notify.'))
            return

        for subscription in subscriptions:
            try:
                send_mail(
                    'Marketplace is Now Live on Corps Connect!',
                    'The marketplace is ready! Visit https://yourdomain.com/marketplace to start buying and selling. Thank you for subscribing!',
                    'essteeooh@gmail.com',
                    [subscription.email],
                    fail_silently=False,
                )
                subscription.notified = True
                subscription.save()
                logger.info(f"Notification sent to {subscription.email}")
            except Exception as e:
                logger.error(f"Failed to send notification to {subscription.email}: {str(e)}")
                continue

        self.stdout.write(self.style.SUCCESS('Successfully notified all subscribed users.'))