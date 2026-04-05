#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asl_project.settings')
django.setup()

from django.contrib.sites.models import Site

def ensure_site_exists():
    """Ensure that site with ID=1 exists"""
    try:
        site = Site.objects.get(id=1)
        print(f"Site already exists: {site.domain}")
    except Site.DoesNotExist:
        # Create the site if it doesn't exist
        site = Site.objects.create(
            id=1,
            domain='127.0.0.1:8000',
            name='ASL Learning App'
        )
        print(f"Created site: {site.domain}")

if __name__ == '__main__':
    ensure_site_exists()
