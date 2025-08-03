from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Follow, PPA, PPAReview, LeaderboardEntry, Notification
from .tasks import notify_follow_task, notify_rating_task, notify_leaderboard_task, notify_followed_post_task
import logging
from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserProfile

logger = logging.getLogger(__name__)



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Follow)
def follow_notification(sender, instance, created, **kwargs):
    if created and instance.followed.profile.notify_follow:
        logger.debug(f"Follow notification triggered for {instance.followed.username} by {instance.follower.username}")
        existing_notification = Notification.objects.filter(
            user=instance.followed,
            type='follow',
            message=f"{instance.follower.username} followed you."
        ).first()
        if existing_notification:
            if not existing_notification.data or not existing_notification.data.get('urls'):
                existing_notification.data = {'urls': {'follower_url': reverse('profile_view', kwargs={'username': instance.follower.username})}}
                existing_notification.save()
                logger.debug(f"Updated existing follow notification for {instance.followed.username} with data: {existing_notification.data}")
            else:
                logger.warning(f"Existing follow notification with data already exists for {instance.followed.username}")
        else:
            notify_follow_task(instance.follower.id, instance.followed.id)

@receiver(post_save, sender=PPAReview)
def rating_notification(sender, instance, created, **kwargs):
    if created and instance.ppa.posted_by.profile.notify_rating:
        existing_notification = Notification.objects.filter(
            user=instance.ppa.posted_by,
            type='rating',
            message=f"{instance.user.username} rated your PPA {instance.rating} stars."
        ).first()
        if existing_notification:
            if not existing_notification.data or not existing_notification.data.get('urls'):
                ppa_id = instance.ppa.id
                existing_notification.data = {'urls': {'rating_url': reverse('ppa_detail', kwargs={'id': ppa_id})}}
                existing_notification.save()
                logger.debug(f"Updated existing rating notification for {instance.ppa.posted_by.username} with data: {existing_notification.data}")
            else:
                logger.warning(f"Existing rating notification with data already exists for {instance.ppa.posted_by.username}")
        else:
            notify_rating_task(instance.user.id, instance.ppa.posted_by.id, instance.rating)


@receiver(post_save, sender=LeaderboardEntry)
def leaderboard_notification(sender, instance, created, **kwargs):
    if not created:  # Only trigger on update, not creation
        try:
            old_entry = LeaderboardEntry.objects.get(pk=instance.pk)
            if old_entry.points != instance.points:  # Check if points changed
                if instance.user.profile.notify_leaderboard:
                    old_rank = LeaderboardEntry.objects.filter(points__gt=old_entry.points).count() + 1
                    new_rank = LeaderboardEntry.objects.filter(points__gt=instance.points).count() + 1
                    if old_rank != new_rank:  # Only notify if rank changed
                        existing_notification = Notification.objects.filter(
                            user=instance.user,
                            type='leaderboard',
                            message=f"You are ranked #{new_rank} on the leaderboard"
                        ).exclude(is_read=True).first()  # Exclude read notifications
                        if existing_notification:
                            if not existing_notification.data or not existing_notification.data.get('urls'):
                                existing_notification.data = {'urls': {'leaderboard_url': reverse('leaderboard')}}
                                existing_notification.save()
                                logger.debug(f"Updated existing leaderboard notification for {instance.user.username} with data: {existing_notification.data}")
                            else:
                                logger.warning(f"Existing leaderboard notification with data already exists for {instance.user.username}")
                        else:
                            notify_leaderboard_task(instance.user.id)
        except LeaderboardEntry.DoesNotExist:
            logger.error(f"LeaderboardEntry with pk {instance.pk} not found for update check")

@receiver(post_save, sender=PPA)
def post_notification(sender, instance, created, **kwargs):
    if created and instance.posted_by.profile.notify_post:
        followers = instance.posted_by.followers.all()
        logger.debug(f"Followers for {instance.posted_by.username}: {[f.follower.username for f in followers]}")
        for follow in followers:
            follower = follow.follower
            logger.debug(f"Checking notification for follower {follower.username}, notify_post: {follower.profile.notify_post}")
            if follower.profile.notify_post:
                existing_notification = Notification.objects.filter(
                    user=follower,
                    type='post',
                    message=f"{instance.posted_by.username} posted a new PPA."
                ).first()
                if existing_notification:
                    if not existing_notification.data or not existing_notification.data.get('urls'):
                        existing_notification.data = {'urls': {'post_url': reverse('ppa_detail', kwargs={'pk': instance.id})}}
                        existing_notification.save()
                        logger.debug(f"Updated existing post notification for {follower.username} with data: {existing_notification.data}")
                    else:
                        logger.warning(f"Existing post notification with data already exists for {follower.username}")
                else:
                    notification = Notification.objects.create(
                        user=follower,
                        message=f"{instance.posted_by.username} posted a new PPA.",
                        type='post',
                        data={'urls': {'post_url': reverse('ppa_detail', kwargs={'pk': instance.id})}}
                    )
                    logger.info(f"Created new post notification for {follower.username}, ID: {notification.id}")
                    notification.save()


