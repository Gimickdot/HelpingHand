from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import redirect
from allauth.exceptions import ImmediateHttpResponse

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Handle social login before it completes.
        Check if email is already used by a regular account.
        If so, redirect to login page with account_exists flag to show popup.
        """
        email = sociallogin.account.extra_data.get('email')
        
        if email:
            # Check if email already exists in regular User model
            if User.objects.filter(email=email).exists():
                # Email already exists with regular account - redirect to login with popup trigger
                response = redirect('/login/?account_exists=true&email=' + email)
                raise ImmediateHttpResponse(response)
        
        return sociallogin
