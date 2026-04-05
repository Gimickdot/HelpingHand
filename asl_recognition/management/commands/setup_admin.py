from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from asl_recognition.models import UserProfile
from django.utils.timezone import now

class Command(BaseCommand):
    help = 'Set up admin user and initial admin data'

    def handle(self, *args, **options):
        # Create superuser if it doesn't exist
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@asl-learning.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            admin_user.set_password('admin123!')
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully created admin user')
            )
        else:
            # Update existing admin user password if needed
            admin_user.set_password('admin123!')
            admin_user.save()
            self.stdout.write(
                self.style.WARNING('Admin user already exists, password updated')
            )
        
        # Create or get UserProfile for admin user
        admin_profile, profile_created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'bio': 'System Administrator',
                'created_at': now(),
                'updated_at': now()
            }
        )
        if profile_created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created admin user profile')
            )
        
        # Create demo admin user
        demo_user, created = User.objects.get_or_create(
            username='demo_admin',
            defaults={
                'email': 'demo@asl-learning.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            demo_user.set_password('admin123!')
            demo_user.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully created demo admin user')
            )
        else:
            # Update existing demo admin user password if needed
            demo_user.set_password('admin123!')
            demo_user.save()
            self.stdout.write(
                self.style.WARNING('Demo admin user already exists, password updated')
            )
        
        # Create or get UserProfile for demo admin user
        demo_profile, profile_created = UserProfile.objects.get_or_create(
            user=demo_user,
            defaults={
                'bio': 'Demo Administrator for testing',
                'created_at': now(),
                'updated_at': now()
            }
        )
        if profile_created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created demo admin user profile')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Admin setup complete!')
        )
        self.stdout.write('Admin URL:')
        self.stdout.write('  Admin Panel: /admin/')
        self.stdout.write('  Analytics: /admin/analytics/')
        self.stdout.write('You can now access the admin panel with:')
        self.stdout.write('  Username: admin | Password: admin123!')
        self.stdout.write('  Username: demo_admin | Password: admin123!')
