import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Setup Google SocialApp for OAuth login'

    def handle(self, *args, **options):
        try:
            site = Site.objects.get(id=1)  # SITE_ID=1
            self.stdout.write('Site(1) found')
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR('Site ID=1 not found. Create with ./manage.py sites --populate or set SITE_ID'))
            return

        self.stdout.write('Google provider slug ready')
        
        # Get credentials from environment variables
        client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
        
        if not client_id or not secret:
            self.stdout.write(self.style.ERROR('GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables must be set'))
            return

        social_app, created = SocialApp.objects.get_or_create(
            provider='google',
            name='Google',
            defaults={
                'client_id': client_id,
                'secret': secret,
            }
        )
        
        if not social_app.sites.filter(id=site.id).exists():
            social_app.sites.add(site)
            self.stdout.write('Site added to SocialApp')

        if created:
            self.stdout.write(self.style.SUCCESS('Google SocialApp created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Google SocialApp already exists, sites updated'))
        
        self.stdout.write(
            self.style.SUCCESS(
                'Setup complete! Redirect URIs in Google Console:\n'
                'http://127.0.0.1:8000/accounts/google/login/callback/\n'
                'Test: http://127.0.0.1:8000/accounts/google/login/'
            )
        )
