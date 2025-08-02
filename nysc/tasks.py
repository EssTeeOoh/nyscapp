from django.contrib.auth.models import User
from .models import Notification, LeaderboardEntry
from django.urls import reverse
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

def notify_follow_task(follower_id, followed_id):
    try:
        follower = User.objects.get(id=follower_id)
        followed = User.objects.get(id=followed_id)
        if followed.profile.notify_follow:
            notification = Notification.objects.create(
                user=followed,
                message=f"{follower.username} followed you.",
                type='follow',
                data={'urls': {'follower_url': reverse('profile_view', kwargs={'username': follower.username})}}
            )
            logger.debug(f"Follow notification created for {followed.username} with data: {notification.data}")
            notification.save()
    except Exception as e:
        logger.error(f"Error creating follow notification for {followed_id}: {str(e)}", exc_info=True)

def notify_rating_task(rater_id, rated_id, rating):
    try:
        rater = User.objects.get(id=rater_id)
        rated = User.objects.get(id=rated_id)
        if rated.profile.notify_rating and rated.ppas.exists():
            ppa_id = rated.ppas.first().id
            notification = Notification.objects.create(
                user=rated,
                message=f"{rater.username} rated your PPA {rating} stars.",
                type='rating',
                data={'urls': {'rating_url': reverse('ppa_detail', kwargs={'id': ppa_id})}}
            )
            logger.debug(f"Rating notification created for {rated.username} with data: {notification.data}")
            notification.save()
    except Exception as e:
        logger.error(f"Error creating rating notification for {rated_id}: {str(e)}", exc_info=True)

def notify_leaderboard_task(user_id):
    try:
        user = User.objects.get(id=user_id)
        if user.profile.notify_leaderboard:
            entry = LeaderboardEntry.objects.get(user=user)
            rank = LeaderboardEntry.objects.filter(points__gt=entry.points).count() + 1
            notification = Notification.objects.create(
                user=user,
                message=f"You are ranked #{rank} on the leaderboard",
                type='leaderboard',
                data={'urls': {'leaderboard_url': reverse('leaderboard')}}
            )
            logger.debug(f"Leaderboard notification created for {user.username} with data: {notification.data}")
            notification.save()
    except Exception as e:
        logger.error(f"Error creating leaderboard notification for {user_id}: {str(e)}", exc_info=True)

def notify_followed_post_task(follower_id, posted_by_id, post_id):
    try:
        follower = User.objects.get(id=follower_id)
        posted_by = User.objects.get(id=posted_by_id)
        if follower.profile.notify_post:
            notification = Notification.objects.create(
                user=follower,
                message=f"{posted_by.username} posted a new PPA.",
                type='post',
                data={'urls': {'post_url': reverse('ppa_detail', kwargs={'id': post_id})}}
            )
            logger.debug(f"Post notification created for {follower.username} with data: {notification.data}")
            notification.save()
    except Exception as e:
        logger.error(f"Error creating post notification for {follower_id}: {str(e)}", exc_info=True)

