from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile
import re


class RegisterForm(UserCreationForm):
    """Form for user registration with validation"""
    email = forms.EmailField(required=True)
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        help_text='Minimum 8 characters: at least 1 number and 1 special character'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists. Please choose a different one.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email is already registered. Use a different email.")
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check for at least one number
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number.")
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\"\\|,.<>\/?]', password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:\"\\|,.<>/?).")
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data


class LoginForm(forms.Form):
    """Form for user login with email"""
    email = forms.EmailField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    username = forms.CharField(
        max_length=150,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
    )
    
    class Meta:
        model = UserProfile
        fields = ('profile_picture', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...', 'style': 'resize: none;'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if username is being changed and if it already exists
        if self.user and username != self.user.username:
            if User.objects.filter(username=username).exists():
                raise ValidationError("Username already exists. Please choose a different one.")
        return username
    
    def save(self, commit=True):
        profile = super(ProfileForm, self).save(commit=False)
        if self.user:
            self.user.username = self.cleaned_data['username']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with validation and confirmation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'id': 'id_old_password'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'id': 'id_new_password1'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'id': 'id_new_password2'})
        self.fields['new_password1'].help_text = 'Minimum 8 characters: at least 1 number and 1 special character'
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check for at least one number
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number.")
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\"\\|,.<>\/?]', password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:\"\\|,.<>/?).")
        
        return password
    
    def clean_new_password2(self):
        """Validate that new password is different from current password"""
        new_password1 = self.cleaned_data.get('new_password1')
        old_password = self.cleaned_data.get('old_password')
        
        if new_password1 and self.user.check_password(new_password1):
            raise forms.ValidationError(
                "Your new password cannot be the same as your current password."
            )
        
        return super().clean_new_password2()
