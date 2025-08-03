# nysc/urls.py


from django.urls import path, include
from .views import (
    PPAListView, PPADetailView, submit_ppa, submit_review, register,
    verify_email, forgot_password, resend_verification, CustomPasswordResetConfirmView,
    set_user_state, profile_view, profile_edit, ppa_edit, CustomLoginView, follow_user, unfollow_user, 
    request_ppa_verification, leaderboard, check_notifications, notifications, clear_notifications, mark_notifications_read, delete_review, marketplace_coming_soon, marketplace_subscribe,
    marketplace_feedback, bookmarks_list, toggle_bookmark, check_bookmark, camp_info, delete_ppa,
    
)
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', PPAListView.as_view(), name='ppa_finder'),
    path('ppa/<int:pk>/', PPADetailView.as_view(), name='ppa_detail'),
    path('submit-ppa/', submit_ppa, name='submit_ppa'),
    path('ppa/<int:ppa_id>/review/', submit_review, name='submit_review'),
    path('ppa/<int:ppa_id>/delete_review/', delete_review, name='delete_review'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='ppa_finder'), name='logout'),
    path('register/', register, name='register'),
    path('verify-email/<uuid:token>/', verify_email, name='verify_email'),
    
    path('set_user_state/', set_user_state, name='set_user_state'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('resend-verification/', resend_verification, name='resend_verification'),
    path('password-reset-confirm/<uuid:token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/', include('social_django.urls', namespace='social')),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/<str:username>/', profile_view, name='profile_view'),
    path('ppa/<int:ppa_id>/delete/', delete_ppa, name='delete_ppa'),
    path('ppa/<int:ppa_id>/edit/', ppa_edit, name='ppa_edit'),
    path('profile/<str:username>/follow/', follow_user, name='follow_user'),
    path('profile/<str:username>/unfollow/', unfollow_user, name='unfollow_user'),
    path('ppa/<int:ppa_id>/verify/', request_ppa_verification, name='request_ppa_verification'),
    path('leaderboard/', leaderboard, name='leaderboard'),  
    path('notifications/', notifications, name='notifications'),
    path('check-notifications/', check_notifications, name='check_notifications'),
    path('clear_notifications/', clear_notifications, name='clear_notifications'),
    path('mark_notifications_read/', mark_notifications_read, name='mark_notifications_read'),
    path('marketplace/', marketplace_coming_soon, name='marketplace_coming_soon'),
    path('marketplace/subscribe/', marketplace_subscribe, name='marketplace_subscribe'),
    path('marketplace/feedback/', marketplace_feedback, name='marketplace_feedback'),
    path('bookmarks/', bookmarks_list, name='bookmarks_list'),
    path('ppa/<int:ppa_id>/toggle-bookmark/', toggle_bookmark, name='toggle_bookmark'),
    path('ppa/<int:ppa_id>/check-bookmark/', check_bookmark, name='check_bookmark'),
    path('camp-info/', camp_info, name='camp_info'),


]
