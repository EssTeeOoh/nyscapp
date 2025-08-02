from django.test import TestCase

# Create your tests here.
import unittest
import datetime
from django.utils import timezone
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from .models import LeaderboardEntry, LeaderboardReset
from .middleware import LeaderboardMiddleware

class ResetSimulationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.entry = LeaderboardEntry.objects.create(user=self.user, points=100, total_ppas=5, verified_ppas=2)
        self.reset = LeaderboardReset.objects.get_or_create(id=1)[0]
        self.reset.last_reset = timezone.now() - datetime.timedelta(days=8)  # Simulate last reset over a week ago
        self.reset.save()

    def test_automatic_reset(self):
        # Simulate a request
        request = self.factory.get('/')
        request.user = self.user
        middleware = LeaderboardMiddleware(lambda r: None)  # Dummy get_response
        
        # Mock time to Sunday, August 3, 2025, 00:00 WAT
        mock_time = timezone.datetime(2025, 8, 3, 0, 0, tzinfo=timezone.get_current_timezone())
        with timezone.override(mock_time):
            middleware.process_request(request)
        
        # Check if reset occurred
        updated_entry = LeaderboardEntry.objects.get(user=self.user)
        updated_reset = LeaderboardReset.objects.get(id=1)
        self.assertEqual(updated_entry.points, 0)
        self.assertTrue(updated_reset.last_reset > mock_time - datetime.timedelta(minutes=1))

    def tearDown(self):
        self.user.delete()
        self.entry.delete()
        self.reset.delete()

if __name__ == '__main__':
    import django
    django.setup()
    unittest.main()