from django.db import models
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import URLValidator
import sys
import logging
import pytesseract
import datetime

logger = logging.getLogger('nysc')  

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    twitter_url = models.URLField(blank=True, validators=[URLValidator(schemes=['https', 'http'])])
    facebook_url = models.URLField(blank=True, validators=[URLValidator(schemes=['https', 'http'])])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True, db_index=True)  # Added with index
    is_public = models.BooleanField(default=True, help_text="Allow user to appear on the leaderboard")
    notify_follow = models.BooleanField(default=False, help_text="Receive notifications when someone follows you.")
    notify_rating = models.BooleanField(default=False, help_text="Receive notifications when a post is rated.")
    notify_leaderboard = models.BooleanField(default=False, help_text="Receive notifications when you appear on the leaderboard.")
    notify_post = models.BooleanField(default=False, help_text="Receive notifications when someone I follow posts.")

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def is_online(self, timeout=300):  # 300 seconds = 5 minutes
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen).total_seconds() < timeout

    def save(self, *args, **kwargs):
        if self.profile_picture:
            try:
                img = Image.open(self.profile_picture)
                img = ImageOps.exif_transpose(img)
                img = img.convert('RGB')
                max_size = (600, 600)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                output = BytesIO()
                img.save(output, format='JPEG', quality=80, optimize=True)
                output.seek(0)
                self.profile_picture = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    f"{self.profile_picture.name.rsplit('.', 1)[0]}_compressed.jpg",
                    'image/jpeg',
                    sys.getsizeof(output),
                    None
                )
            except Exception as e:
                logger.error(f"Profile picture processing error: {e}")
        super().save(*args, **kwargs)


class LeaderboardReset(models.Model):
    last_reset = models.DateTimeField(null=True, blank=True, default=None)

    def __str__(self):
        return f"Last Reset: {self.last_reset}"

class LeaderboardEntryManager(models.Manager):
    def reset_leaderboard(self):
        entries = self.all()
        for entry in entries:
            entry.points = 0
            entry.total_ppas = 0
            entry.verified_ppas = 0
            entry.save()
        reset, created = LeaderboardReset.objects.get_or_create(id=1)
        reset.last_reset = timezone.now()
        reset.save()
        logger.info(f"Leaderboard reset at {timezone.now()}")

class LeaderboardEntry(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Changed to OneToOneField
    points = models.IntegerField(default=0)
    total_ppas = models.IntegerField(default=0)
    verified_ppas = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    objects = LeaderboardEntryManager()

    class Meta:
        ordering = ['-points', '-total_ppas']

    def __str__(self):
        return f"{self.user.username} - {self.points} points"

    def save(self, *args, **kwargs):
        # Ensure no custom logic interferes
        super().save(*args, **kwargs)

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')  # Prevent duplicate follows
        indexes = [
            models.Index(fields=['follower', 'followed']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        return self.expires_at > timezone.now()

    def __str__(self):
        return f"Token for {self.user.email}"

class PPA(models.Model):
    name = models.CharField(max_length=200)
    state = models.CharField(max_length=50, choices=[
        ('Abia', 'Abia'), ('Abuja', 'Abuja'), ('Adamawa', 'Adamawa'),
        ('Akwa Ibom', 'Akwa Ibom'), ('Anambra', 'Anambra'), ('Bauchi', 'Bauchi'),
        ('Bayelsa', 'Bayelsa'), ('Benue', 'Benue'), ('Borno', 'Borno'),
        ('Cross River', 'Cross River'), ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'),
        ('Edo', 'Edo'), ('Ekiti', 'Ekiti'), ('Enugu', 'Enugu'),
        ('Gombe', 'Gombe'), ('Imo', 'Imo'), ('Jigawa', 'Jigawa'),
        ('Kaduna', 'Kaduna'), ('Kano', 'Kano'), ('Katsina', 'Katsina'),
        ('Kebbi', 'Kebbi'), ('Kogi', 'Kogi'), ('Kwara', 'Kwara'),
        ('Lagos', 'Lagos'), ('Nasarawa', 'Nasarawa'), ('Niger', 'Niger'),
        ('Ogun', 'Ogun'), ('Ondo', 'Ondo'), ('Osun', 'Osun'),
        ('Oyo', 'Oyo'), ('Plateau', 'Plateau'), ('Rivers', 'Rivers'),
        ('Sokoto', 'Sokoto'), ('Taraba', 'Taraba'), ('Yobe', 'Yobe'),
        ('Zamfara', 'Zamfara')
    ])
    lga = models.CharField(max_length=100)
    sector = models.CharField(max_length=100, choices=[
        ('Education', 'Education'),
        ('Health', 'Health'),
        ('Government', 'Government'),
        ('Banking', 'Banking'),
        ('Tech', 'Technology'),
        ('NGO', 'Non-Governmental Organization'),
        ('Oil and Gas', 'Oil and Gas'),
        ('Media', 'Media'),
        ('Agriculture', 'Food and Agriculture'),
        ('Legal', 'Legal'),
        ('Manufacturing', 'Manufacturing'),
        ('Hospitality', 'Hospitality'),
        ('Telecommunications', 'Telecommunications'),
        ('Private', 'Other Private Sector'),
    ])
    stipend = models.IntegerField(null=True, blank=True)
    accommodation_available = models.BooleanField(null=True, blank=True)  # Allow NULL
    description = models.TextField(blank=True)
    contact = models.CharField(max_length=200, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ppas')
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='ppa_images/')
    address = models.CharField(max_length=255)
    verified = models.BooleanField(default=False, help_text="Set to True after admin verification")
    verification_document = models.ImageField(upload_to='ppa_verifications/', null=True, blank=True, help_text="Upload PPA posting letter or clearance letter or clear photo of PPA for verification")
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('not_submitted', 'Not Submitted'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='not_submitted',
        help_text="Status of verification request"
    )

    class Meta:
        # Ensure no duplicate PPAs with the same name and address across all users
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'address'],
                name='unique_ppa_name_address'
            )
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.image:
                try:
                    img = Image.open(self.image)
                    img = ImageOps.exif_transpose(img)
                    img = img.convert('RGB')
                    target_ratio = 3 / 2
                    width, height = img.size
                    current_ratio = width / height
                    if current_ratio > target_ratio:
                        new_width = int(height * target_ratio)
                        left = (width - new_width) // 2
                        img = img.crop((left, 0, left + new_width, height))
                    elif current_ratio < target_ratio:
                        new_height = int(width / target_ratio)
                        top = (height - new_height) // 2
                        img = img.crop((0, top, width, top + new_height))
                    max_size = (300, 300)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    output = BytesIO()
                    img.save(output, format='JPEG', quality=85, optimize=True)
                    output.seek(0)
                    self.image = InMemoryUploadedFile(
                        output,
                        'ImageField',
                        f"{self.image.name.rsplit('.', 1)[0]}_compressed.jpg",
                        'image/jpeg',
                        sys.getsizeof(output),
                        None
                    )
                except Exception as e:
                    print(f"PPA image processing error: {e}")

            # Only process verification if a new document is uploaded and status allows
            if (self.verification_document and self.verification_status == 'not_submitted') or \
               (self.verification_document and self.verification_status == 'rejected'):
                try:
                    doc_img = Image.open(self.verification_document)
                    doc_img = doc_img.convert('L')  # Convert to grayscale
                    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust path
                    extracted_text = pytesseract.image_to_string(doc_img).lower()

                    ppa_name = self.name.lower()
                    ppa_state = self.state.lower()
                    ppa_lga = self.lga.lower()
                    ppa_address = self.address.lower()

                    # More strict validation
                    if (ppa_name in extracted_text and ppa_state in extracted_text) or \
                       (ppa_lga in extracted_text and ppa_address in extracted_text):
                        self.verified = True
                        self.verification_status = 'approved'
                        print(f"OCR successfully verified PPA {self.name}")
                    else:
                        self.verified = False
                        self.verification_status = 'pending'  # Trigger manual review
                        print(f"OCR could not fully verify PPA {self.name}, pending manual review")
                except Exception as e:
                    print(f"OCR processing error for PPA {self.name}: {e}")
                    self.verified = False
                    self.verification_status = 'pending'

            super().save(*args, **kwargs)

            # Update leaderboard only if not within 24 hours of last reset
            last_reset = LeaderboardReset.objects.filter(id=1).values_list('last_reset', flat=True).first()
            if not last_reset or (timezone.now() > last_reset + timezone.timedelta(hours=24)):
                entry, created = LeaderboardEntry.objects.select_for_update().get_or_create(user=self.posted_by)
                entry.total_ppas = self.posted_by.ppas.count()
                entry.verified_ppas = self.posted_by.ppas.filter(verified=True).count()
                entry.points = (entry.total_ppas * 10) + (entry.verified_ppas * 20)
                entry.save()
                logger.info(f"Updated LeaderboardEntry for {self.posted_by.username} post-PPA save")
            else:
                logger.debug(f"Skipped leaderboard update for {self.posted_by.username} due to recent reset at {last_reset}")

    def average_rating(self):
        reviews = self.reviews.all()
        return sum(review.rating for review in reviews) / reviews.count() if reviews else 0

    def __str__(self):
        return f"{self.name} - {self.state}"

class PPAReview(models.Model):
    ppa = models.ForeignKey(PPA, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ppa.name} ({self.rating} stars)"
    


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict, blank=True, null=True)  # Simplified data structure
    type = models.CharField(
        max_length=50,
        choices=[
            ('follow', 'Follow'),
            ('rating', 'Rating'),
            ('leaderboard', 'Leaderboard'),
            ('post', 'Post from Followed'),
        ]
    )

    class Meta:
        indexes = [models.Index(fields=['user', 'is_read', 'created_at'])]

    def __str__(self):
        return f"{self.user.username} - {self.type} ({self.created_at})"

    @property
    def is_expired(self):
        """Check if notification is older than 24 hours since being read."""
        if self.is_read:
            return datetime.datetime.now(datetime.timezone.utc) > self.created_at + datetime.timedelta(hours=24)
        return False
    


class MarketplaceSubscription(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    def __str__(self):
        return self.email
    

class MarketplaceFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Feedback from {self.user.username if self.user else 'Anonymous'} at {self.created_at}"
    

class UserBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    ppa = models.ForeignKey('PPA', on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'ppa')  
        indexes = [models.Index(fields=['user', 'ppa'])]  # Optimize lookup

    def __str__(self):
        return f"{self.user.username} bookmarked {self.ppa.name}"