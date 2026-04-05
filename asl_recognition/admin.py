from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Max, Min
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.timezone import now, timedelta
from .models import GameScore, UserProfile


@admin.register(GameScore)
class GameScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'game_mode_display', 'created_at')
    list_filter = ('game_mode', 'created_at')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def game_mode_display(self, obj):
        color = '#fd7e14' if obj.game_mode == 'sprint' else '#6f42c1'
        icon = '⚡' if obj.game_mode == 'sprint' else '🎯'
        mode_display = obj.get_game_mode_display()
        return format_html('<span style="color: {}; background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 4px;">{} {}</span>', color, icon, mode_display)
    game_mode_display.short_description = 'Mode'
    
    def user(self, obj):
        return obj.user.username if obj.user else 'Anonymous'
    user.short_description = 'User'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'total_games', 'high_score', 'avg_score', 'favorite_mode', 'created_at', 'profile_completion')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_display(self, obj):
        return obj.user.username if obj.user else 'Anonymous'
    user_display.short_description = 'User'
    
    def total_games(self, obj):
        return obj.user.gamescore_set.count()
    total_games.short_description = 'Total Games'
    
    def high_score(self, obj):
        high_score = obj.user.gamescore_set.aggregate(Max('score'))['score__max'] or 0
        return high_score
    high_score.short_description = 'High Score'
    
    def avg_score(self, obj):
        avg_score = obj.user.gamescore_set.aggregate(Avg('score'))['score__avg'] or 0
        return round(avg_score, 1)
    avg_score.short_description = 'Average Score'
    
    def favorite_mode(self, obj):
        games = obj.user.gamescore_set.all()
        if games:
            mode_counts = {}
            for game in games:
                mode_counts[game.game_mode] = mode_counts.get(game.game_mode, 0) + 1
            favorite = max(mode_counts, key=mode_counts.get) if mode_counts else 'standard'
            return favorite
        return 'N/A'
    favorite_mode.short_description = 'Favorite Mode'
    
    def profile_completion(self, obj):
        completion = 0
        if obj.bio:
            completion += 50
        if obj.user.gamescore_set.exists():
            completion += 50
        return f"{completion}%"
    profile_completion.short_description = 'Profile Complete'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('user__gamescore_set')


# Custom admin site with analytics
class ASLAdminSite(admin.AdminSite):
    site_header = 'ASL Learning Admin'
    site_title = 'ASL Admin Portal'
    index_title = 'Dashboard'
    login_template = 'admin/admin_login.html'
    index_template = 'admin/analytics_dashboard.html'
    
    def each_context(self, request):
        context = super().each_context(request)
        context['dark_admin_css'] = '/static/admin/css/dark_admin.css'
        return context
    
    def index(self, request, extra_context=None):
        # Check if user is authenticated and has admin privileges
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return self.login(request)
        
        # Get analytics context and pass to parent index method
        # The parent method will render index_template with this context
        analytics_context = self.get_analytics_context(request)
        
        # Merge with any extra_context provided
        if extra_context:
            analytics_context.update(extra_context)
        
        # Call parent's index method which will use index_template
        # This ensures proper admin layout with sidebar is rendered
        return super().index(request, extra_context=analytics_context)
    
    def get_analytics_context(self, request):
        """Get analytics data for dashboard"""
        from django.db.models import Count, Avg, Max, Min
        from django.utils.timezone import now, timedelta
        
        # Basic stats
        total_users = User.objects.count()
        total_games = GameScore.objects.count()
        
        # Game mode stats
        sprint_count = GameScore.objects.filter(game_mode='sprint').count()
        standard_count = GameScore.objects.filter(game_mode='standard').count()
        
        # Recent activity
        recent_scores = GameScore.objects.select_related('user').order_by('-created_at')[:10]
        
        # Performance metrics
        high_score = GameScore.objects.aggregate(Max('score'))['score__max'] or 0
        avg_score = GameScore.objects.aggregate(Avg('score'))['score__avg'] or 0
        
        # Calculate percentages
        total_games_count = total_games
        sprint_percentage = (sprint_count / total_games_count * 100) if total_games_count > 0 else 0
        standard_percentage = (standard_count / total_games_count * 100) if total_games_count > 0 else 0
        high_score_percentage = (high_score / 100) if high_score > 0 else 0
        
        # Games this week
        week_ago = now() - timedelta(days=7)
        games_this_week = GameScore.objects.filter(created_at__gte=week_ago).count()
        
        # Games today
        today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
        games_today = GameScore.objects.filter(created_at__gte=today_start).count()
        
        # Active users today
        active_users_today = User.objects.filter(
            gamescore__created_at__gte=now() - timedelta(days=1)
        ).distinct().count()
        
        # Active users 7 days
        active_users_7_days = User.objects.filter(
            gamescore__created_at__gte=now() - timedelta(days=7)
        ).distinct().count()
        
        # Calculate percentages safely
        games_this_week_percentage = (games_this_week / total_games_count * 100) if total_games_count > 0 else 0
        games_today_percentage = (games_today / total_games_count * 100) if total_games_count > 0 else 0
        active_users_percentage = (active_users_today / total_users * 100) if total_users > 0 else 0
        active_users_7_days_percentage = (active_users_7_days / total_users * 100) if total_users > 0 else 0
        avg_score_percentage = min((avg_score / high_score * 100), 100) if high_score > 0 else 0
        
        return {
            'title': 'ASL Learning Analytics Dashboard',
            'total_users': total_users,
            'total_games': total_games,
            'sprint_count': sprint_count,
            'standard_count': standard_count,
            'sprint_percentage': round(sprint_percentage, 1),
            'standard_percentage': round(standard_percentage, 1),
            'high_score': high_score,
            'high_score_percentage': round(high_score_percentage, 1),
            'avg_score': round(avg_score, 1),
            'avg_score_percentage': round(avg_score_percentage, 1),
            'games_this_week': games_this_week,
            'games_this_week_percentage': round(games_this_week_percentage, 1),
            'games_today': games_today,
            'games_today_percentage': round(games_today_percentage, 1),
            'active_users_today': active_users_today,
            'active_users_percentage': round(active_users_percentage, 1),
            'active_users_7_days': active_users_7_days,
            'active_users_7_days_percentage': round(active_users_7_days_percentage, 1),
            'recent_scores': recent_scores,
            'app_list': self.get_app_list(request),
        }
    
    def analytics_view(self, request):
        """Analytics dashboard view - for backward compatibility"""
        return self.index(request)
    
    def get_urls(self):
        from django.urls import path
        from asl_recognition import views
        
        urls = super().get_urls()
        # Replace the default login/logout URLs with our custom ones
        custom_urls = [
            path('login/', views.admin_login, name='login'),
            path('logout/', views.admin_logout, name='logout'),
            path('api/stats/', self.admin_view(self.api_stats), name='api_stats'),
        ]
        
        # Filter out the default login/logout URLs and add our custom ones
        filtered_urls = [url for url in urls if 'login/' not in str(url.pattern) and 'logout/' not in str(url.pattern)]
        return custom_urls + filtered_urls
    
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        
        # Add ASL Learning Dashboard link
        dashboard_item = {
            'models': [{
                'name': 'Analytics Dashboard',
                'object_name': 'analytics_dashboard',
                'admin_url': '/admin/',
                'view_only': True,
            }]
        }
        
        # Insert dashboard at the beginning
        app_list.insert(0, {
            'name': 'Dashboard',
            'app_label': 'dashboard',
            'models': dashboard_item['models'],
            'has_module_perms': True,
            'app_url': '/admin/',
            'models': dashboard_item['models'],
        })
        
        return app_list
    
    def analytics_view(self, request):
        """Analytics dashboard view"""
        from django.db.models import Count, Avg, Max, Min
        from django.utils.timezone import now, timedelta
        
        # Basic stats
        total_users = User.objects.count()
        total_games = GameScore.objects.count()
        
        # Game mode stats
        sprint_count = GameScore.objects.filter(game_mode='sprint').count()
        standard_count = GameScore.objects.filter(game_mode='standard').count()
        
        # Recent activity
        recent_scores = GameScore.objects.select_related('user').order_by('-created_at')[:10]
        
        # Performance metrics
        high_score = GameScore.objects.aggregate(Max('score'))['score__max'] or 0
        avg_score = GameScore.objects.aggregate(Avg('score'))['score__avg'] or 0
        
        # Calculate percentages
        total_games_count = total_games
        sprint_percentage = (sprint_count / total_games_count * 100) if total_games_count > 0 else 0
        standard_percentage = (standard_count / total_games_count * 100) if total_games_count > 0 else 0
        high_score_percentage = (high_score / 100)  # Assuming max possible score is 100
        
        # Games this week
        week_ago = now() - timedelta(days=7)
        games_this_week = GameScore.objects.filter(created_at__gte=week_ago).count()
        
        # Active users today
        active_users_today = User.objects.filter(
            gamescore__created_at__gte=now() - timedelta(days=1)
        ).distinct().count()
        
        # Active users 7 days
        active_users_7_days = User.objects.filter(
            gamescore__created_at__gte=now() - timedelta(days=7)
        ).distinct().count()
        
        # Calculate percentages safely
        games_this_week_percentage = (games_this_week / total_games_count * 100) if total_games_count > 0 else 0
        active_users_percentage = (active_users_today / total_users * 100) if total_users > 0 else 0
        active_users_7_days_percentage = (active_users_7_days / total_users * 100) if total_users > 0 else 0
        avg_score_percentage = min((avg_score / high_score * 100), 100) if high_score > 0 else 0
        
        context = {
            'total_users': total_users,
            'total_games': total_games,
            'sprint_count': sprint_count,
            'standard_count': standard_count,
            'sprint_percentage': round(sprint_percentage, 1),
            'standard_percentage': round(standard_percentage, 1),
            'high_score': high_score,
            'high_score_percentage': round(high_score_percentage, 1),
            'avg_score': round(avg_score, 1),
            'avg_score_percentage': round(avg_score_percentage, 1),
            'games_this_week': games_this_week,
            'games_this_week_percentage': round(games_this_week_percentage, 1),
            'active_users_today': active_users_today,
            'active_users_percentage': round(active_users_percentage, 1),
            'active_users_7_days': active_users_7_days,
            'active_users_7_days_percentage': round(active_users_7_days_percentage, 1),
            'recent_scores': recent_scores,
        }
        
        return render(request, 'admin/analytics_dashboard.html', context)
    
    def api_stats(self, request):
        # API endpoint for real-time stats
        from django.utils.timezone import now, timedelta
        stats = {
            'total_users': User.objects.count(),
            'active_users_today': User.objects.filter(
                gamescore__created_at__gte=now() - timedelta(days=1)
            ).distinct().count(),
            'games_today': GameScore.objects.filter(
                created_at__gte=now() - timedelta(days=1)
            ).count(),
            'games_this_week': GameScore.objects.filter(
                created_at__gte=now() - timedelta(days=7)
            ).count(),
            'avg_score': GameScore.objects.aggregate(
                avg=Avg('score')
            )['avg'] or 0,
        }
        return JsonResponse(stats)


# Create the custom admin site instance
admin_site = ASLAdminSite()

# Override the default admin site
admin.site = admin_site

# Register models with the admin site
admin.site.register(GameScore, GameScoreAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(User)  # Django's built-in User model

# Unregister SocialToken (Social application tokens) from admin
# This must run after allauth has registered its models
def unregister_social_token():
    try:
        from allauth.socialaccount.models import SocialToken
        if SocialToken in admin.site._registry:
            admin.site.unregister(SocialToken)
            print("✓ SocialToken unregistered successfully")
        else:
            print("✗ SocialToken not found in admin registry")
    except Exception as e:
        print(f"✗ Error unregistering SocialToken: {e}")

# Run immediately
unregister_social_token()

# Also try with delay to ensure allauth has loaded
from django.apps import apps
if apps.ready:
    unregister_social_token()
