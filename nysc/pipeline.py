# nyscapp/nysc/pipeline.py
import logging
from django.core.exceptions import PermissionDenied
from nysc.models import UserProfile

logger = logging.getLogger(__name__)

def create_user_profile(backend, user, response, *args, **kwargs):
    logger.info(f"Creating profile for user {user.username} via {backend.name}")
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    if created:
        logger.info(f"New profile created for user {user.username}")
        user_profile.save()  # Ensure the profile is saved with default values
    # For Google OAuth, assume email is verified
    if backend.name == 'google-oauth2':
        logger.info(f"Setting is_active=True for Google user {user.username}")
        user.is_active = True  # Mark as active since Google verifies email
        user.save()
    return {'user': user}

def check_user_active(backend, user, response, *args, **kwargs):
    logger.info(f"Checking activity for user {user.username} via {backend.name}, is_active: {user.is_active}")
    # Skip email verification check for Google OAuth
    if user and not user.is_active and backend.name != 'google-oauth2':
        logger.warning(f"User {user.username} is inactive and not Google-authenticated, raising PermissionDenied")
        raise PermissionDenied('Please verify your email before logging in.')
    return {'user': user}