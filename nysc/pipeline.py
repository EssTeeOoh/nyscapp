# nyscapp/nysc/pipeline.py
import logging
from django.core.exceptions import PermissionDenied
from nysc.models import UserProfile

logger = logging.getLogger(__name__)

def create_user_profile(backend, user, response, *args, **kwargs):
    logger.info(f"Processing profile for user {user.username} via {backend.name}")
    # Check if profile exists (signal should handle creation)
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    if created:
        logger.info(f"Profile created for {user.username} via pipeline (unexpected, signal should handle)")
    # Handle Google OAuth specific logic
    if backend.name == 'google-oauth2':
        logger.info(f"Setting is_active=True for Google user {user.username}")
        user.is_active = True
        user.save()
    return {'user': user}

def check_user_active(backend, user, response, *args, **kwargs):
    logger.info(f"Checking activity for user {user.username} via {backend.name}, is_active: {user.is_active}")
    if user and not user.is_active and backend.name != 'google-oauth2':
        logger.warning(f"User {user.username} is inactive and not Google-authenticated, raising PermissionDenied")
        raise PermissionDenied('Please verify your email before logging in.')
    return {'user': user}