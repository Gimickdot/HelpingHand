import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import Provider, SocialApp

class Command(BaseCommand):
    help = 'Setup Google SocialApp for OAuth login'

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)  # SITE_ID=1
        provider = Provider.objects.get(code='google')
        
        # Get credentials from environment variables
        client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
        
        if not client_id or not secret:
            self.stdout.write(self.style.ERROR('GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables must be set'))
            return
        
        social_app, created = SocialApp.objects.get_or_create(
            provider=provider,
            name='Google',
            defaults={
                'client_id': client_id,
                'secret': secret,
            }
        )
        
        if not social_app.sites.filter(id=site.id).exists():
            social_app.sites.add(site)
        
        if created:
            self.stdout.write(self.style.SUCCESS('Google SocialApp created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Google SocialApp already exists, sites updated'))
        self.stdout.write('Redirect URIs in Google Console must include: http://127.0.0.1:8000/accounts/google/login/callback/')
