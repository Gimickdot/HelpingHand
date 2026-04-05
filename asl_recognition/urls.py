from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('webcam/', views.webcam, name='webcam'),
    path('webcam_backup/', views.webcam_backup, name='webcam_backup'),
    path('api/predict/', views.predict, name='predict'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('home/', views.home, name='home'),
    path('learn/', views.learn, name='learn'),
    path('game/', views.game, name='game'),
    path('api/save-score/', views.save_score, name='save_score'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.view_user_profile, name='view_user_profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('delete-profile-picture/', views.delete_profile_picture, name='delete_profile_picture'),
    path('confirm-password-change/<str:token>/', views.confirm_password_change, name='confirm_password_change'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('accounts/login/success/', views.social_login_success, name='social_login_success'),
    # Custom password reset URLs (must be before allauth to override)
    path('accounts/password/reset/', views.custom_password_reset, name='account_reset_password'),
    path('accounts/password/reset/confirm/<uidb64>/<token>/', views.custom_password_reset_confirm, name='password_reset_confirm'),
    # Admin authentication URLs
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
]
