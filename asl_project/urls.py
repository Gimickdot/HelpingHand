"""ASL Project URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from asl_recognition.admin import admin_site

def health_check(request):
    """Health check endpoint for Render"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'asl-learning-app'
    })

urlpatterns = [
    path('admin/', admin_site.urls),
    path('health/', health_check, name='health'),
    # Include asl_recognition URLs first to override allauth password reset
    path('', include('asl_recognition.urls')),
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
