from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from .models import LeaderboardEntry, LeaderboardReset, Notification
from django.utils import timezone
import datetime

class UpdateLastSeenMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_update = {}

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            user_id = request.user.id
            current_time = timezone.now()
            if user_id not in self.last_update or (current_time - self.last_update[user_id]).total_seconds() > 300:
                request.user.profile.last_seen = current_time
                request.user.profile.save(update_fields=['last_seen'])
                self.last_update[user_id] = current_time
        return response

class LeaderboardMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update or create leaderboard entry only if PPA counts have changed
            entry, created = LeaderboardEntry.objects.get_or_create(user=request.user)
            new_total_ppas = request.user.ppas.count()
            new_verified_ppas = request.user.ppas.filter(verified=True).count()
            new_points = (new_total_ppas * 10) + (new_verified_ppas * 20)

            if entry.total_ppas != new_total_ppas or entry.verified_ppas != new_verified_ppas:
                entry.total_ppas = new_total_ppas
                entry.verified_ppas = new_verified_ppas
                entry.points = new_points
                entry.save()

                # Check for rank milestones only if points changed
                if entry.user.profile.notify_leaderboard:
                    leaderboard = LeaderboardEntry.objects.order_by('-points')[:10]
                    if entry in leaderboard:
                        rank = next((i + 1 for i, e in enumerate(leaderboard) if e.id == entry.id), None)
                        if rank:
                            last_notified_rank = request.session.get('last_notified_rank')
                            milestones = [10, 3, 2, 1]
                            should_notify = False
                            message = ""

                            if last_notified_rank is None and rank <= 10:
                                should_notify = True
                                message = f"You have entered the top 10! You are ranked #{rank} on the leaderboard!"
                            elif last_notified_rank and rank != last_notified_rank:
                                if rank in milestones and rank < last_notified_rank:
                                    should_notify = True
                                    message = f"You are now ranked #{rank} on the leaderboard!"
                                elif rank > 3 and last_notified_rank <= 3:
                                    should_notify = True
                                    message = f"You have dropped below top 3. Current rank: #{rank}."

                            if should_notify:
                                Notification.objects.create(
                                    user=entry.user,
                                    message=message,
                                    type='leaderboard',
                                    is_read=False
                                )
                                request.session['last_notified_rank'] = rank
                            elif rank > 10:
                                if 'last_notified_rank' in request.session:
                                    del request.session['last_notified_rank']

        return None