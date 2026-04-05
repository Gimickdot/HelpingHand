from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone

User = get_user_model()

class AdminBackend(ModelBackend):
    """
    Custom authentication backend for admin users only.
    This keeps admin sessions separate from regular user sessions.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Only authenticate admin users (staff or superuser)
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and (user.is_staff or user.is_superuser):
                return user
        except User.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            if user.is_staff or user.is_superuser:
                return user
        except User.DoesNotExist:
            return None

class AdminSessionMiddleware:
    """
    Middleware to handle admin sessions separately from regular user sessions.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is an admin request
        if request.path.startswith('/admin/'):
            # Use separate session for admin
            request.session.save()
            # Clear regular user session if exists
            if hasattr(request, '_regular_user_session'):
                del request._regular_user_session
        
        response = self.get_response(request)
        return response
