from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import PPA, PPAReview, EmailVerificationToken, UserProfile, LeaderboardEntry, Notification, Follow, MarketplaceSubscription, MarketplaceFeedback, UserBookmark
from .forms import PPASearchForm, PPASubmissionForm, PPAReviewForm, RegistrationForm, EmailAuthenticationForm, ForgotPasswordForm, ResendVerificationForm, ProfileForm, UserForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
import uuid
from .models import LeaderboardReset
from datetime import timedelta
import datetime
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json
from pathlib import Path
from django.http import HttpResponseForbidden
import logging
import os
from .utils import lgasData
from .utils import get_state_from_coords
from django.template.loader import render_to_string
from django.core.cache import cache
from django.conf import settings
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Avg
from django.views.decorators.cache import never_cache
logger = logging.getLogger(__name__)

'''@login_required
@csrf_exempt
def geocode_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            lat = data.get('lat')
            lon = data.get('lon')
            if lat and lon:
                api_key = os.getenv('OPENCAGE_API_KEY')
                if not api_key:
                    return JsonResponse({'error': 'OpenCage API key not configured'}, status=500)
                url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={api_key}"
                response = requests.get(url)
                if response.status_code == 200:
                    result = response.json()
                    return JsonResponse(result)
                else:
                    return JsonResponse({'error': f'Geocoding failed with status {response.status_code}: {response.text}'}, status=500)
            return JsonResponse({'error': 'Invalid data'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except requests.RequestException as e:
            return JsonResponse({'error': f'Request failed: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)'''

@login_required
def camp_info(request):
    cache_key = 'camp_data'
    camp_data = cache.get(cache_key)
    if not camp_data:
        json_path = os.path.join(settings.STATICFILES_DIRS[0], 'nysc', 'json', 'camp_data.json')
        with open(json_path, 'r') as f:
            camp_data = json.load(f)
        cache.set(cache_key, camp_data, timeout=86400)

    camp_items = [
        {"category": "Essentials", "items": [
            "Original Call-up Letter", "NYSC Green Card", "Passport Photographs (8 copies)",
            "Medical Fitness Certificate", "Valid ID Card"
        ]},
        {"category": "Clothing", "items": [
            "White T-shirts and Shorts", "White Tennis Shoes", "White Socks",
            "Bed Sheets and Pillowcases", "Toiletries (toothbrush, toothpaste, soap, etc.)"
        ]},
        {"category": "Food and Water", "items": [
            "Reusable Water Bottle", "Non-perishable Snacks (e.g., biscuits, nuts)",
            "Cooking Utensils (if allowed)", "Detergent and Bucket"
        ]},
        {"category": "Prohibited Items", "items": [
            "Electronic Devices (unless permitted)", "Alcohol", "Weapons",
            "Excess Cash", "Perishable Food"
        ]},
        {"category": "Recommended Purchases", "items": [
            "Insect Repellent", "Torchlight or Headlamp", "Umbrella or Raincoat",
            "Small First Aid Kit", "Power Bank"
        ]}
    ]

    links = [
        {"text": "JAMB Portal", "url": "https://www.jamb.gov.ng"},
        {"text": "NYSC Portal", "url": "https://www.nysc.gov.ng"},
        {"text": "NYSC Orientation Camp Guidelines", "url": "https://www.nysc.gov.ng/camp-guidelines"}
    ]

    context = {
        'camp_data': camp_data,
        'camp_items': camp_items,
        'links': links,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY if hasattr(settings, 'GOOGLE_MAPS_API_KEY') else ''
    }
    return render(request, 'nysc/camp_info.html', context)

@login_required
@require_GET
def check_bookmark(request, ppa_id):
    try:
        ppa = PPA.objects.get(id=ppa_id)
        is_bookmarked = UserBookmark.objects.filter(user=request.user, ppa=ppa).exists()
        return JsonResponse({'status': 'success', 'is_bookmarked': is_bookmarked})
    except PPA.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'PPA not found'}, status=404)

@login_required
def toggle_bookmark(request, ppa_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            ppa = get_object_or_404(PPA, id=ppa_id)
            bookmark, created = UserBookmark.objects.get_or_create(user=request.user, ppa=ppa)
            if not created:
                bookmark.delete()
                action = 'removed'
                message = 'Bookmark removed.'
            else:
                action = 'added'
                message = 'Bookmark added.'
            logger.info(f"User {request.user.username} {action} bookmark for PPA {ppa.name}")
            return JsonResponse({'status': 'success', 'action': action, 'message': message})
        except Exception as e:
            logger.error(f"Error toggling bookmark for PPA {ppa_id}: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

@login_required
def bookmarks_list(request):
    bookmarks = UserBookmark.objects.filter(user=request.user).select_related('ppa')
    return render(request, 'nysc/bookmarks.html', {'bookmarks': bookmarks})

def marketplace_coming_soon(request):
    if not request.user.is_authenticated and not settings.DEBUG:
        messages.warning(request, "Please log in to access this page.")
        return redirect('login')
    return render(request, 'nysc/marketplace_coming_soon.html')

@require_POST
@csrf_protect
def marketplace_subscribe(request):
    logger.info(f"Received {request.method} request to /marketplace/subscribe/ from {request.META.get('REMOTE_ADDR')}")
    if not request.user.is_authenticated and not settings.DEBUG:
        logger.warning("Unauthenticated access attempt to subscribe")
        return JsonResponse({'status': 'error', 'message': 'Please log in to subscribe.'}, status=403)
    
    email = request.POST.get('email')
    if not email:
        logger.error("No email provided in request")
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    
    try:
        if MarketplaceSubscription.objects.filter(email=email).exists():
            logger.info(f"Duplicate subscription attempt for {email}")
            return JsonResponse({'status': 'error', 'message': 'This email is already subscribed.'}, status=400)
        
        subscription = MarketplaceSubscription.objects.create(email=email)
        logger.info(f"New subscription saved: {email} by user {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return JsonResponse({'status': 'success', 'message': 'You will be notified when the marketplace is ready!'})
    except Exception as e:
        logger.error(f"Error subscribing email {email}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'An error occurred. Please try again.'}, status=500)

@require_POST
@csrf_protect
def marketplace_feedback(request):
    if not request.user.is_authenticated and not settings.DEBUG:
        return JsonResponse({'status': 'error', 'message': 'Please log in to submit feedback.'}, status=403)
    
    feedback = request.POST.get('feedback')
    if not feedback:
        return JsonResponse({'status': 'error', 'message': 'Feedback is required.'}, status=400)
    
    try:
        feedback_instance = MarketplaceFeedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            feedback=feedback,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        logger.info(f"Feedback from {request.user.email if request.user.is_authenticated else 'Anonymous'}: {feedback}")
        return JsonResponse({'status': 'success', 'message': 'Thank you for your feedback!'})
    except Exception as e:
        logger.error(f"Error submitting feedback from {request.user.email if request.user.is_authenticated else 'Anonymous'}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'An error occurred. Please try again.'}, status=500)

@login_required
def check_notifications(request):
    unread_count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'unread_count': unread_count})

@login_required
def mark_notifications_read(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logger.debug(f"mark_notifications_read request: {request.POST}, headers: {request.headers}")
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = get_object_or_404(Notification, id=notification_id, user=request.user)
                notification.is_read = True
                notification.save()
                logger.info(f"Notification {notification_id} marked as read for user {request.user.username}")
                return JsonResponse({'status': 'success'})
            except Exception as e:
                logger.error(f"Error marking notification {notification_id} as read: {str(e)}", exc_info=True)
                return JsonResponse({'status': 'error', 'message': f'Failed to mark notification as read: {str(e)}'}, status=400)
        else:
            try:
                unread_notifications = request.user.notifications.filter(is_read=False)
                if unread_notifications.exists():
                    unread_notifications.update(is_read=True)
                    logger.info(f"All unread notifications marked as read for user {request.user.username}")
                now = timezone.now()
                expired_notifications = request.user.notifications.filter(
                    is_read=True,
                    created_at__lt=now - datetime.timedelta(hours=24)
                )
                if expired_notifications.exists():
                    expired_notifications.delete()
                    logger.info(f"Cleared {expired_notifications.count()} expired notifications for user {request.user.username}")
                return JsonResponse({'status': 'success'})
            except Exception as e:
                logger.error(f"Error marking all notifications as read: {str(e)}", exc_info=True)
                return JsonResponse({'status': 'error', 'message': f'Failed to mark notifications as read: {str(e)}'}, status=400)
    logger.warning("Invalid request method or missing XMLHttpRequest header for mark_notifications_read")
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@login_required
def notifications(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    now = datetime.datetime.now(datetime.timezone.utc)
    expired_notifications = [n for n in notifications if n.is_read and now > n.created_at + datetime.timedelta(hours=24)]
    if expired_notifications:
        for notification in expired_notifications:
            notification.delete()
        logger.info(f"Expired notifications cleared for user {request.user.username} on page load")
    return render(request, 'nysc/notifications.html', {'notifications': notifications})

@login_required
@require_POST
def clear_notifications(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            Notification.objects.filter(user=request.user).delete()
            logger.info(f"All notifications cleared for user {request.user.username}")
            return JsonResponse({'status': 'success', 'message': 'All notifications cleared.'})
        except Exception as e:
            logger.error(f"Error clearing notifications for user {request.user.username}: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': f'Failed to clear notifications: {str(e)}'}, status=400)
    logger.warning("Missing XMLHttpRequest header for clear_notifications")
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@login_required
def request_ppa_verification(request, ppa_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            ppa = get_object_or_404(PPA, id=ppa_id, posted_by=request.user)
            if ppa.verification_status == 'pending':
                return JsonResponse({
                    'status': 'error',
                    'message': 'A verification request is already pending.'
                }, status=400)

            if 'verification_document' in request.FILES:
                ppa.verification_document = request.FILES['verification_document']
                ppa.verification_status = 'pending'
                ppa.save()

                if ppa.verified and ppa.verification_status == 'approved' and ppa.verification_document:
                    if hasattr(ppa.verification_document, 'path') and os.path.exists(ppa.verification_document.path):
                        os.remove(ppa.verification_document.path)
                        ppa.verification_document = None
                        ppa.save(update_fields=['verification_document'])

                return JsonResponse({
                    'status': 'success',
                    'message': 'Verification request submitted. Processing may take a moment.',
                    'verified': ppa.verified,
                    'verification_status': ppa.verification_status
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please upload a verification document.'
                }, status=400)
        except Exception as e:
            logger.error(f"Error in request_ppa_verification for PPA {ppa_id}: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred.'
            }, status=500)
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request.'
    }, status=400)

class CustomLoginView(LoginView):
    template_name = 'nysc/login.html'
    authentication_form = EmailAuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        logger.debug(f"Attempting to log in user: {user.username}, is_active: {user.is_active}, is_authenticated: {user.is_authenticated}")
        try:
            login(self.request, user, backend='nysc.backends.EmailAuthBackend')
            logger.info(f"User {user.username} logged in successfully, is_active: {user.is_active}")
            if self.request.user.is_authenticated:
                logger.debug(f"Session set for user: {self.request.user.username}, session ID: {self.request.session.session_key}")
                if 'last_notified_rank' in self.request.session:
                    del self.request.session['last_notified_rank']
                return redirect('ppa_finder')
            else:
                logger.error(f"Session not set for user: {user.username} after login.")
                messages.error(self.request, 'Login failed due to session issue. Please try again.')
                return self.render_to_response(self.get_context_data(form=form))
        except Exception as e:
            logger.error(f"Login error for user {user.username}: {str(e)}")
            messages.error(self.request, 'An error occurred during login. Please try again.')
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        logger.warning(f"Failed login attempt: {form.errors}")
        messages.error(self.request, 'Invalid email or password.')
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return '/'

@login_required
def follow_user(request, username):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'POST' and is_ajax:
        try:
            user_to_follow = get_object_or_404(User, username=username)
            if user_to_follow == request.user:
                return JsonResponse({'status': 'error', 'message': 'You cannot follow yourself.'}, status=400)
            
            follow = Follow.objects.filter(follower=request.user, followed=user_to_follow).first()
            if follow:
                follow.delete()
                logger.info(f"User {request.user.username} unfollowed {user_to_follow.username}")
                return JsonResponse({
                    'status': 'success',
                    'action': 'unfollowed',
                    'followers_count': user_to_follow.followers.count()
                })
            else:
                follow = Follow.objects.create(follower=request.user, followed=user_to_follow)
                logger.info(f"User {request.user.username} followed {user_to_follow.username}")
                return JsonResponse({
                    'status': 'success',
                    'action': 'followed',
                    'followers_count': user_to_follow.followers.count()
                })
        except User.DoesNotExist:
            logger.error(f"User {username} not found in follow_user")
            return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error in follow_user for {username}: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

@login_required
def unfollow_user(request, username):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.method == 'POST' and is_ajax:
        try:
            user_to_unfollow = get_object_or_404(User, username=username)
            deleted, _ = Follow.objects.filter(follower=request.user, followed=user_to_unfollow).delete()
            if deleted:
                logger.info(f"User {request.user.username} unfollowed {user_to_unfollow.username}")
                return JsonResponse({
                    'status': 'success',
                    'action': 'unfollowed',
                    'followers_count': user_to_unfollow.followers.count()
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Not following this user.'}, status=400)
        except User.DoesNotExist:
            logger.error(f"User {username} not found in unfollow_user")
            return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error in unfollow_user for {username}: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': 'An error occurred.'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

@login_required
def profile_view(request, username):
    logger.debug(f"Profile view accessed for username: {username} by user: {request.user}")
    try:
        user = get_object_or_404(User, username=username)
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            logger.info(f"Created new profile for user: {username}")
        ppas = PPA.objects.filter(posted_by=user).order_by('-created_at')
        is_following = Follow.objects.filter(follower=request.user, followed=user).exists() if request.user.is_authenticated and request.user != user else False
        if not user.is_active:
            logger.warning(f"User {user.username} is inactive, redirecting to login")
            messages.error(request, 'Your account is not active. Please verify your email.')
            return redirect('login')
        logger.debug(f"Rendering profile for user {user.username}, is_owner: {request.user == user}")
        return render(request, 'nysc/profile.html', {
            'profile': profile,
            'ppas': ppas,
            'is_owner': request.user == user,
            'is_following': is_following,
            'posts_count': ppas.count(),
            'followers_count': user.followers.count(),
            'following_count': user.following.count(),
        })
    except Exception as e:
        logger.error(f"Error in profile_view for username {username}: {str(e)}")
        messages.error(request, "Unable to load profile.")
        return redirect('ppa_finder')

@login_required
def delete_ppa(request, ppa_id):
    ppa = get_object_or_404(PPA, id=ppa_id, posted_by=request.user)
    if request.method == 'POST':
        ppa.delete()
        last_reset = LeaderboardReset.objects.filter(id=1).values_list('last_reset', flat=True).first()
        if not last_reset or (timezone.now() > last_reset + timezone.timedelta(hours=24)):
            entry, _ = LeaderboardEntry.objects.get_or_create(user=request.user)
            entry.total_ppas = request.user.ppas.count()
            entry.verified_ppas = request.user.ppas.filter(verified=True).count()
            entry.points = (entry.total_ppas * 10) + (entry.verified_ppas * 20)
            entry.save()
        return JsonResponse({'status': 'success', 'message': 'PPA deleted'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def profile_edit(request):
    logger.debug(f"Profile edit accessed by user: {request.user}")
    
    if not request.user.is_authenticated:
        logger.error("Unauthenticated user attempted to access profile_edit")
        messages.error(request, "You must be logged in to edit your profile.")
        return redirect('login')

    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if created:
            logger.info(f"Created new profile for user: {request.user.username}")
        
        if request.method == 'POST':
            user_form = UserForm(request.POST, instance=request.user)
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                logger.info(f"Profile updated for user: {request.user.username}")
                return redirect('profile_view', username=request.user.username)
            else:
                logger.warning(f"Invalid form submission for user: {request.user.username}, errors: {user_form.errors} {profile_form.errors}")
                messages.error(request, 'Please correct the errors below.')
        else:
            user_form = UserForm(instance=request.user)
            profile_form = ProfileForm(instance=profile)
        
        if not request.user.is_active:
            logger.warning(f"User {request.user.username} is inactive, redirecting to login")
            messages.error(request, 'Your account is not active. Please verify your email.')
            return redirect('login')
        
        logger.debug(f"Rendering profile_edit for user {request.user.username}")
        return render(request, 'nysc/profile_edit.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {request.user}")
        messages.error(request, "Profile data not found. Please contact support.")
        return redirect('ppa_finder')
    except Exception as e:
        logger.error(f"Error in profile_edit for user {request.user}: {str(e)}")
        messages.error(request, "An error occurred while loading the profile edit page.")
        return redirect('ppa_finder')

@login_required
def ppa_edit(request, ppa_id):
    ppa = get_object_or_404(PPA, id=ppa_id, posted_by=request.user)
    if request.method == 'POST':
        form = PPASubmissionForm(request.POST, request.FILES, instance=ppa)
        if form.is_valid():
            form.save()
            return redirect('profile_view', username=request.user.username)
    else:
        form = PPASubmissionForm(instance=ppa)
    return render(request, 'nysc/ppa_edit.html', {'form': form, 'ppa': ppa})

@csrf_exempt
def set_user_state(request):
    if request.method == 'POST':
        try:
            # Prefer JSON body over POST data
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            logger.debug(f"Received data in set_user_state: {data}")
            lat = data.get('lat')
            lon = data.get('lon')
            if lat is not None and lon is not None:
                lat, lon = float(lat), float(lon)
                logger.info(f"Processing geolocation: lat={lat}, lon={lon}")
                state = get_state_from_coords(lat, lon)
                if state:
                    request.session['user_state'] = state
                    request.session.modified = True
                    logger.info(f"User state set to {state} for session {request.session.session_key}")
                    return JsonResponse({'status': 'success', 'state': state})
                logger.warning(f"No state found for coordinates: {lat}, {lon}")
                return JsonResponse({'status': 'error', 'message': 'No state found for given coordinates'}, status=400)
            return JsonResponse({'status': 'error', 'message': 'Missing lat or lon'}, status=400)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data in set_user_state: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Invalid request data'}, status=400)
        except ValueError as e:
            logger.error(f"Invalid coordinate values: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Invalid coordinate format'}, status=400)
        except Exception as e:
            logger.error(f"Error in set_user_state: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

class PPAListView(ListView):
    model = PPA
    template_name = 'nysc/ppa_finder.html'
    context_object_name = 'ppas'
    paginate_by = 8

    def get_queryset(self):
        queryset = PPA.objects.filter(is_approved=True)
        form = PPASearchForm(self.request.GET)
        user_state = self.request.session.get('user_state')

        logger.debug(f"Session user_state: {user_state}")
        logger.debug(f"Form is valid: {form.is_valid()}")
        logger.debug(f"Raw GET data: {self.request.GET}")
        logger.debug(f"Form errors: {form.errors}")

        if form.is_valid():
            state = form.cleaned_data.get('state')
            lga = form.cleaned_data.get('lga')
            sector = form.cleaned_data.get('sector')
            min_stipend = form.cleaned_data.get('min_stipend')
            accommodation = form.cleaned_data.get('accommodation')

            logger.debug(f"Form data: state={state}, lga={lga}, sector={sector}, min_stipend={min_stipend}, accommodation={accommodation}")

            if state:
                queryset = queryset.filter(state__iexact=state)
                logger.debug(f"Applied state filter: {state}")
                if lga and lga != '' and state in lgasData and lga in lgasData[state]:
                    queryset = queryset.filter(lga__iexact=lga)
                    logger.debug(f"Applied lga filter: {lga} for state {state}")
            if sector:
                queryset = queryset.filter(sector__iexact=sector)
                logger.debug(f"Applied sector filter: {sector}")
            if min_stipend and min_stipend != '':
                stipend_threshold = int(min_stipend)
                queryset = queryset.filter(stipend__gte=stipend_threshold)
                logger.debug(f"Applied min_stipend filter: >= {stipend_threshold}")
            if accommodation:
                if accommodation == 'yes':
                    queryset = queryset.filter(accommodation_available=True)
                    logger.debug(f"Applied accommodation filter: Yes")
                elif accommodation == 'no':
                    queryset = queryset.filter(accommodation_available=False)
                    logger.debug(f"Applied accommodation filter: No")
        elif user_state and not self.request.GET:
            queryset = queryset.filter(state__iexact=user_state)
            logger.debug(f"Applied default user_state filter: {user_state}")

        queryset = queryset.annotate(avg_rating=Avg('reviews__rating'))

        logger.debug(f"Final queryset: {queryset.query}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PPASearchForm(self.request.GET)
        context['form'] = form
        context['user_state'] = self.request.session.get('user_state')
        context['states'] = [state[0] for state in PPA.state.field.choices]

        featured_ppas = PPA.objects.filter(
            is_approved=True
        ).annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=4).order_by('-avg_rating')[:3]

        context['featured_ppas'] = featured_ppas

        context['page_obj'] = context.get('page_obj')
        context['is_paginated'] = context.get('is_paginated')
        context['paginator'] = context.get('paginator')

        if self.request.user.is_authenticated:
            context['bookmarked_ppa_ids'] = self.request.user.bookmarks.values_list('ppa_id', flat=True)
            context['unread_notification_count'] = self.request.user.notifications.filter(is_read=False).count()
        else:
            context['bookmarked_ppa_ids'] = []
            context['unread_notification_count'] = 0

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            ppas_html = ''.join([
                render_to_string('nysc/ppa_card.html', {'ppa': ppa, 'request': self.request})
                for ppa in context['ppas']
            ])
            return JsonResponse({
                'success': True,
                'html': ppas_html,
                'has_previous': context['page_obj'].has_previous(),
                'has_next': context['page_obj'].has_next(),
                'current_page': context['page_obj'].number,
                'total_pages': context['paginator'].num_pages
            })
        return super().render_to_response(context, **response_kwargs)

class PPADetailView(LoginRequiredMixin, DetailView):
    model = PPA
    template_name = 'nysc/ppa_detail.html'
    context_object_name = 'ppa'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ppa = self.get_object()
        existing_review = ppa.reviews.filter(user=self.request.user).first()
        
        if existing_review and 'edit' in self.request.GET and self.request.GET['edit'] == str(existing_review.id):
            context['review_form'] = PPAReviewForm(instance=existing_review)
            context['is_edit'] = True
        else:
            context['review_form'] = PPAReviewForm()
            context['is_edit'] = False
        
        context['existing_review'] = existing_review
        if 'review_form' not in context or context['review_form'] is None:
            print("Warning: review_form is None or not in context!")

        context['bookmarked_ppa_ids'] = self.request.user.bookmarks.values_list('ppa_id', flat=True)

        return context

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                user_profile, created = UserProfile.objects.get_or_create(user=user)
                if not created:
                    logger.warning(f"UserProfile already exists for user: {user.username}")
                token = EmailVerificationToken.objects.create(user=user)
                verify_url = request.build_absolute_uri(
                    reverse('verify_email', kwargs={'token': str(token.token)})
                )
                send_mail(
                    'Verify Your NYSC Connect Account',
                    f'Click this link to verify your email: {verify_url}\nThis link expires in 24 hours.',
                    'yourusername@gmail.com',
                    [user.email],
                    fail_silently=False,
                )
                request.session['show_verification_modal'] = True
                logger.info(f"User {user.username} registered successfully, verification email sent.")
                return redirect('register')
            except Exception as e:
                logger.error(f"Error during registration for user {form.cleaned_data['username']}: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            logger.warning(f"Invalid registration form submission: {form.errors}")
    else:
        form = RegistrationForm()
    show_verification_modal = request.session.pop('show_verification_modal', False)
    return render(request, 'nysc/register.html', {
        'form': form,
        'show_verification_modal': show_verification_modal
    })

def verify_email(request, token):
    try:
        token_obj = EmailVerificationToken.objects.get(token=token)
        if token_obj.is_valid():
            user = token_obj.user
            user.is_active = True
            user.save()
            token_obj.delete()
            messages.success(request, 'Your email has been verified! Please log in.')
            return redirect('login')
        else:
            token_obj.delete()
            messages.error(request, 'This verification link has expired.')
            return redirect('register')
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('register')

@login_required
@never_cache
def leaderboard(request):
    limit = 30
    entries = LeaderboardEntry.objects.filter(
        user__profile__is_public=True,
        total_ppas__gt=0
    ).select_related('user__profile').order_by('-points')[:limit]
    context = {
        'entries': list(entries),
        'max_limit': limit,
    }
    for entry in context['entries']:
        entry.is_following = Follow.objects.filter(follower=request.user, followed=entry.user).exists()
    return render(request, 'nysc/leaderboard.html', context)

def get_badge(rank):
    if rank == 1:
        return 'gold'
    elif rank == 2:
        return 'silver'
    elif rank == 3:
        return 'bronze'
    return None

@login_required
def submit_ppa(request):
    if request.method == 'POST':
        form = PPASubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            ppa = form.save(commit=False)
            ppa.posted_by = request.user
            if not ppa.verification_document:
                ppa.verification_status = 'not_submitted'
            ppa.save()
            entry, _ = LeaderboardEntry.objects.get_or_create(user=request.user)
            last_reset = LeaderboardReset.objects.filter(id=1).values_list('last_reset', flat=True).first()
            if not last_reset or (timezone.now() > last_reset + timezone.timedelta(hours=24)):
                entry.total_ppas = request.user.ppas.count()
                entry.verified_ppas = request.user.ppas.filter(verified=True).count()
                entry.points = (entry.total_ppas * 10) + (entry.verified_ppas * 20)
                entry.save()
            rank = LeaderboardEntry.objects.filter(points__gt=entry.points).count() + 1
            return redirect('ppa_finder')
        else:
            messages.error(request, 'Please correct the errors below.')
            for error in form.errors.values():
                print(error)
    else:
        form = PPASubmissionForm()
    return render(request, 'nysc/submit_ppa.html', {'form': form})

@login_required
def submit_review(request, ppa_id):
    ppa = get_object_or_404(PPA, id=ppa_id)
    existing_review = ppa.reviews.filter(user=request.user).first()

    if request.method == 'POST':
        logger.info("Received POST request: %s", dict(request.POST))
        if 'edit_review' in request.POST and existing_review:
            form = PPAReviewForm(request.POST, instance=existing_review)
            logger.info("Editing existing review with instance: %s", existing_review)
        elif existing_review:
            post_data = request.POST.copy()
            if 'rating' not in post_data and 'comment' not in post_data:
                messages.error(request, "No changes detected. Please update rating or comment.")
                return redirect('ppa_detail', pk=ppa.id)
            form = PPAReviewForm(post_data, instance=existing_review)
            logger.info("Updating existing review with instance: %s", existing_review)
        else:
            form = PPAReviewForm(request.POST)
            logger.info("Creating new review")

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.ppa = ppa
            if not review.rating and 'rating' in request.POST:
                rating = request.POST.get('rating')
                if rating:
                    review.rating = int(rating)
            if not review.comment and 'comment' in request.POST:
                review.comment = request.POST.get('comment')
            if existing_review:
                if not review.rating:
                    review.rating = existing_review.rating
                if not review.comment:
                    review.comment = existing_review.comment
            review.save()
            logger.info("Review saved successfully: %s", review)
            return redirect('ppa_detail', pk=ppa.id)
        else:
            logger.error("Form validation failed: %s", form.errors)
            messages.error(request, "There was an error with your review. Please try again.")
    else:
        if 'edit' in request.GET and existing_review and request.GET['edit'] == str(existing_review.id):
            form = PPAReviewForm(instance=existing_review)
            logger.info("Loading edit form for review: %s", existing_review)
        else:
            form = PPAReviewForm()
            logger.info("Loading new review form")

    return render(request, 'nysc/ppa_detail.html', {
        'ppa': ppa,
        'review_form': form,
        'existing_review': existing_review,
        'is_edit': 'edit' in request.GET and existing_review and request.GET['edit'] == str(existing_review.id)
    })

@login_required
def delete_review(request, ppa_id):
    ppa = get_object_or_404(PPA, id=ppa_id)
    review = ppa.reviews.filter(user=request.user).first()
    if review:
        review.delete()
    return redirect('ppa_detail', pk=ppa.id)

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = EmailVerificationToken.objects.create(user=user, expires_at=timezone.now() + timedelta(minutes=30))
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'token': str(token.token)})
                )
                send_mail(
                    'Reset Your NYSC Connect Password',
                    f'Click this link to reset your password: {reset_url}\nThis link expires in 30 minutes.',
                    'yourusername@gmail.com',
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'A password reset link has been sent to your email.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
                return redirect('login')
    return redirect('login')

def resend_verification(request):
    if request.method == 'POST':
        form = ResendVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email=email)
                if user.is_active:
                    messages.error(request, 'This account is already verified.')
                else:
                    recent_tokens = EmailVerificationToken.objects.filter(
                        user=user,
                        created_at__gte=timezone.now() - timedelta(minutes=5)
                    )
                    if recent_tokens.exists():
                        messages.error(request, 'Please wait 5 minutes before requesting another verification email.')
                    else:
                        token = EmailVerificationToken.objects.create(user=user)
                        verify_url = request.build_absolute_uri(
                            reverse('verify_email', kwargs={'token': str(token.token)})
                        )
                        send_mail(
                            'Verify Your NYSC Connect Account',
                            f'Click this link to verify your email: {verify_url}\nThis link expires in 24 hours.',
                            'yourusername@gmail.com',
                            [email],
                            fail_silently=False,
                        )
                        messages.success(request, 'A new verification email has been sent.')
                return redirect('register')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
                return redirect('register')
    return redirect('register')

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'nysc/password_reset_confirm.html'
    success_url = '/login/'
    post_reset_login = True

    def form_valid(self, form):
        response = super().form_valid(form)
        return response