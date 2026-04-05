from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
import json

class DualSessionMiddleware(MiddlewareMixin):
    """
    Middleware to handle separate sessions for admin and regular users
    """
    
    def process_request(self, request):
        # Check if this is an admin request
        is_admin_path = request.path.startswith('/admin/')
        
        # Skip for static files and media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
            
        # Handle admin session separately
        if is_admin_path:
            # Look for admin session cookie
            admin_session_id = request.COOKIES.get('admin_session_id')
            
            if admin_session_id:
                try:
                    # Load admin session
                    admin_session = SessionStore(session_key=admin_session_id)
                    admin_user_id = admin_session.get('admin_user_id')
                    
                    if admin_user_id:
                        # Set admin user in request
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        admin_user = User.objects.get(id=admin_user_id)
                        
                        # Create a mock authenticated user for admin
                        request.admin_user = admin_user
                        request.is_admin_authenticated = True
                        
                        # IMPORTANT: Don't replace the session - just add admin context
                        # This preserves CSRF tokens and normal session handling
                        request._admin_session = admin_session
                        
                except:
                    # Invalid admin session, clear it
                    request.admin_user = None
                    request.is_admin_authenticated = False
            else:
                request.admin_user = None
                request.is_admin_authenticated = False
        else:
            # Regular user path - use normal session
            request.admin_user = None
            request.is_admin_authenticated = False
            
        return None
    
    def process_response(self, request, response):
        # Handle admin session saving
        if hasattr(request, '_admin_session') and hasattr(request, '_admin_session', 'modified') and request._admin_session.modified:
            request._admin_session.save()
            
        return response
