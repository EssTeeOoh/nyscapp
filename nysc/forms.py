from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import PPA, PPAReview, UserProfile
import requests
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import re
from .utils import lgasData




class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return username



class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'bio', 'twitter_url', 'facebook_url', 'is_public', 'notify_follow', 'notify_rating', 'notify_leaderboard', 'notify_post']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/username or https://x.com/username'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/username'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_follow': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_rating': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_leaderboard': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_post': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_twitter_url(self):
        twitter_url = self.cleaned_data.get('twitter_url')
        if twitter_url:
            if not (twitter_url.startswith('https://twitter.com/') or twitter_url.startswith('https://x.com/')):
                raise forms.ValidationError("Please enter a valid Twitter/X URL (e.g., https://twitter.com/username or https://x.com/username).")
            if twitter_url.startswith('https://x.com/'):
                twitter_url = 'https://twitter.com/' + twitter_url[len('https://x.com/'):]
        return twitter_url

    def clean_facebook_url(self):
        facebook_url = self.cleaned_data.get('facebook_url')
        if facebook_url and not (facebook_url.startswith('https://facebook.com/') or facebook_url.startswith('https://www.facebook.com/')):
            raise forms.ValidationError("Please enter a valid Facebook URL (e.g., https://facebook.com/username).")
        return facebook_url



class PPASearchForm(forms.Form):
    state = forms.ChoiceField(
        choices=[('', 'All States')] + list(PPA.state.field.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_search_state'})
    )
    lga = forms.ChoiceField(
        choices=[('', 'All LGAs')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_search_lga'})
    )
    sector = forms.ChoiceField(
        choices=[('', 'All Sectors')] + list(PPA.sector.field.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_stipend = forms.ChoiceField(
        choices=[
            ('', 'Any Amount'),
            ('100000', '>100k'),
            ('50000', '>50k'),
            ('20000', '>20k')
        ],
        required=False,
        label='Minimum Stipend',
        initial='',  # Default to 'Any Amount'
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_min_stipend'})
    )
    accommodation = forms.ChoiceField(
        choices=[
            ('', 'Any'),
            ('yes', 'Yes'),
            ('no', 'No')
        ],
        required=False,
        label='Accommodation',
        initial='',  # Default to 'Any'
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_accommodation'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set lga choices based on state from GET data
        state = self.data.get('state') or self.initial.get('state')
        if state and state in lgasData:
            self.fields['lga'].choices = [('', 'All LGAs')] + [(lga, lga) for lga in lgasData[state]]
        else:
            self.fields['lga'].choices = [('', 'All LGAs')]





class PPASubmissionForm(forms.ModelForm):
    verification_status = forms.ChoiceField(
        choices=PPA._meta.get_field('verification_status').choices,
        initial='not_submitted',
        widget=forms.HiddenInput(),
        required=False
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Email (Optional)',
        help_text='Provide an email for follow-up (optional).'
    )

    accommodation_available = forms.ChoiceField(
        choices=[
            ('', 'Not Sure'),
            ('yes', 'Yes'),
            ('no', 'No')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Is accommodation provided?'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lga'].choices = [('', 'Select LGA')]
        self.fields['address'].required = True
        self.fields['image'].required = False
        print("LGA choices initialized as Select LGA")

    lga = forms.CharField(
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_lga'})
    )

    class Meta:
        model = PPA
        fields = ['name', 'state', 'lga', 'sector', 'stipend', 'accommodation_available', 'description', 'contact', 'image', 'address', 'verification_status', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control', 'id': 'id_state'}),
            'sector': forms.Select(attrs={'class': 'form-control'}),
            'stipend': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'verification_status': forms.HiddenInput(),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        state = cleaned_data.get('state')
        lga = cleaned_data.get('lga')
        if not lga or lga == '':
            raise forms.ValidationError("Please select an LGA.")
        if state and lga and lga != '':
            print(f"Accepting LGA: {lga} for state: {state} (frontend validated)")
        return cleaned_data

    def clean_accommodation_available(self):
        accommodation = self.cleaned_data.get('accommodation_available')
        if accommodation == 'yes':
            return True
        elif accommodation == 'no':
            return False
        return None  # For 'Not Sure' or empty

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            try:
                img = Image.open(image)
                img = img.convert('RGB')
                max_size = (800, 800)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                output = BytesIO()
                img.save(output, format='JPEG', quality=70, optimize=True)
                output.seek(0)
                compressed_image = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    f"{image.name.rsplit('.', 1)[0]}_compressed.jpg",
                    'image/jpeg',
                    sys.getsizeof(output),
                    None
                )
                print(f"Compressed image: {compressed_image.name}, size: {compressed_image.size} bytes")
                return compressed_image
            except Exception as e:
                print(f"Image compression error: {e}")
                raise forms.ValidationError("Invalid image file.")
        return image

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        # Handle default avatar if no image is uploaded
        if not self.cleaned_data.get('image'):
            name = self.cleaned_data.get('name', 'PPA')
            first_letter = name[0].upper() if name else 'P'
            # Generate a simple avatar (this is a placeholder; you might want to use a library like Pillow)
            from django.core.files.base import ContentFile
            from io import BytesIO
            from PIL import Image, ImageDraw, ImageFont

            # Create a square image
            size = (200, 200)
            image = Image.new('RGB', size, color=(108, 117, 125))  # Default gray color from your CSS
            draw = ImageDraw.Draw(image)
            try:
                font = ImageFont.load_default()  # Use default font; consider adding a custom font
                text_size = draw.textlength(first_letter, font=font)
                position = ((size[0] - text_size) / 2, (size[1] - font.size) / 2)
                draw.text(position, first_letter, fill=(248, 249, 250), font=font)  # White text
                output = BytesIO()
                image.save(output, format='JPEG', quality=70)
                output.seek(0)
                instance.image.save(f'{name}_avatar.jpg', ContentFile(output.read()), save=False)
            except Exception as e:
                print(f"Avatar generation error: {e}")
                # Fallback to no image if generation fails
                pass
        return super().save(*args, **kwargs)
    

class PPAReviewForm(forms.ModelForm):
    class Meta:
        model = PPAReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
        help_text='Required. 30 characters or fewer. Letters, digits, and @/./+/-/_ only.'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter an alphanumeric password, e.g., Password123'
        }),
        help_text='Your password must be at least 8 characters long and contain both letters and numbers (e.g., Password123).'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your alphanumeric password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError('Username can only contain letters, digits, and @/./+/-/_ characters.')
        return username


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise forms.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise forms.ValidationError('Please verify your email before logging in.')
            self.user_cache = user
        return cleaned_data

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))

class ResendVerificationForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))