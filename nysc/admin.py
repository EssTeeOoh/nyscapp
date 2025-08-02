from django.contrib import admin
from django.utils import timezone
from .models import UserProfile, LeaderboardReset, LeaderboardEntry, Follow, EmailVerificationToken, PPA, PPAReview, Notification, MarketplaceSubscription, MarketplaceFeedback, UserBookmark
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Existing UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio_preview', 'twitter_url', 'has_profile_picture', 'updated_at')
    search_fields = ('user__username', 'user__email', 'bio')
    readonly_fields = ('created_at', 'updated_at')

    def bio_preview(self, obj):
        return obj.bio[:50] + '...' if len(obj.bio) > 50 else obj.bio
    bio_preview.short_description = 'Bio'

    def has_profile_picture(self, obj):
        return bool(obj.profile_picture)
    has_profile_picture.boolean = True
    has_profile_picture.short_description = 'Profile Picture'

# Custom UserAdmin with inlines for related models
class PPAInline(admin.TabularInline):
    model = PPA
    extra = 0
    readonly_fields = ('created_at', 'verification_document')
    fields = ('name', 'state', 'lga', 'sector', 'stipend', 'accommodation_available', 'is_approved', 'verified', 'verification_status', 'created_at')

class PPAReviewInline(admin.TabularInline):
    model = PPAReview
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('ppa', 'rating', 'comment', 'created_at')

class LeaderboardEntryInline(admin.TabularInline):
    model = LeaderboardEntry
    extra = 0
    readonly_fields = ('points', 'total_ppas', 'verified_ppas', 'last_updated')
    fields = ('points', 'total_ppas', 'verified_ppas', 'last_updated')

class NotificationInline(admin.TabularInline):
    model = Notification
    extra = 0
    readonly_fields = ('created_at', 'data')
    fields = ('message', 'type', 'created_at', 'is_read', 'data')

class FollowInline(admin.TabularInline):
    model = Follow
    fk_name = 'follower'  # Show users this user follows
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('followed', 'created_at')

class FollowedByInline(admin.TabularInline):
    model = Follow
    fk_name = 'followed'  # Show users following this user
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('follower', 'created_at')

class UserBookmarkInline(admin.TabularInline):
    model = UserBookmark
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('ppa', 'created_at')

class CustomUserAdmin(UserAdmin):
    inlines = [PPAInline, PPAReviewInline, LeaderboardEntryInline, NotificationInline, FollowInline, FollowedByInline, UserBookmarkInline]
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    readonly_fields = ('date_joined',)

# Unregister the default UserAdmin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Existing PPA Admin with Pytesseract status check
@admin.register(PPA)
class PPAAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'lga', 'sector', 'stipend', 'accommodation_available', 'is_approved', 'verified', 'verification_status', 'posted_by', 'created_at')
    list_filter = ('state', 'sector', 'is_approved', 'verified', 'verification_status', 'accommodation_available', 'created_at')
    search_fields = ('name', 'state', 'lga', 'description', 'address')
    list_editable = ('is_approved', 'verified', 'verification_status')
    readonly_fields = ('created_at', 'verification_document')
    fieldsets = (
        (None, {
            'fields': ('name', 'posted_by', 'is_approved', 'verified', 'verification_status')
        }),
        ('Location', {
            'fields': ('state', 'lga', 'address')
        }),
        ('Details', {
            'fields': ('sector', 'stipend', 'accommodation_available', 'description', 'contact', 'image')
        }),
        ('Verification', {
            'fields': ('verification_document',)
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    actions = ['approve_ppas', 'reject_ppas', 'verify_ppas', 'reject_verification', 'check_pytesseract_status']

    def approve_ppas(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Selected PPAs have been approved.")
    approve_ppas.short_description = "Approve selected PPAs"

    def reject_ppas(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, "Selected PPAs have been rejected.")
    reject_ppas.short_description = "Reject selected PPAs"

    def verify_ppas(self, request, queryset):
        queryset.update(verified=True, verification_status='approved')
        self.message_user(request, "Selected PPAs have been verified.")
    verify_ppas.short_description = "Verify selected PPAs"

    def reject_verification(self, request, queryset):
        queryset.update(verified=False, verification_status='rejected')
        self.message_user(request, "Verification for selected PPAs has been rejected.")
    reject_verification.short_description = "Reject verification"

    def check_pytesseract_status(self, request, queryset):
        try:
            from PIL import Image
            import pytesseract
            # Test with a dummy image or existing verification document
            test_image = Image.new('L', (100, 100))
            pytesseract.image_to_string(test_image)
            self.message_user(request, "Pytesseract is installed and working.")
        except Exception as e:
            self.message_user(request, f"Pytesseract is not working: {str(e)}", level='ERROR')
    check_pytesseract_status.short_description = "Check Pytesseract Status"

# Existing PPAReview Admin
@admin.register(PPAReview)
class PPAReviewAdmin(admin.ModelAdmin):
    list_display = ('ppa', 'user', 'rating', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at', 'ppa__state')
    search_fields = ('ppa__name', 'user__email', 'comment')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('ppa', 'user', 'rating', 'comment')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'

# Existing EmailVerificationToken Admin
@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_valid')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('created_at', 'expires_at', 'token')

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'

# New LeaderboardReset Admin
@admin.register(LeaderboardReset)
class LeaderboardResetAdmin(admin.ModelAdmin):
    list_display = ('last_reset',)
    readonly_fields = ('last_reset',)

# New LeaderboardEntry Admin
@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'total_ppas', 'verified_ppas', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-points', '-total_ppas')
    actions = ['reset_leaderboard']

    def reset_leaderboard(self, request, queryset):
        for entry in queryset:
            entry.points = 0
            entry.save()
        reset, created = LeaderboardReset.objects.get_or_create(id=1)
        reset.last_reset = timezone.now()
        reset.save()
        self.message_user(request, "Selected leaderboard entries have been reset.")
    reset_leaderboard.short_description = "Reset selected leaderboard entries"

# New Follow Admin
@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followed', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'followed__username')
    readonly_fields = ('created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'type', 'created_at', 'is_read', 'data')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    list_editable = ('is_read',)
    readonly_fields = ('created_at', 'data')

    def data(self, obj):
        return str(obj.data) if obj.data else 'None'
    data.short_description = 'Data'

# Existing MarketplaceSubscription Admin
@admin.register(MarketplaceSubscription)
class MarketplaceSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'notified')
    search_fields = ('email',)
    list_filter = ('notified', 'created_at')
    ordering = ('-created_at',)

# Existing MarketplaceFeedback Admin
@admin.register(MarketplaceFeedback)
class MarketplaceFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'feedback', 'created_at', 'ip_address')
    search_fields = ('feedback', 'user__username', 'user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False