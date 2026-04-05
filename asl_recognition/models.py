from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

# Create your models here if needed for storing ASL recognition history, etc.
# For now, this app uses the existing ML models without database storage

class ASLRecognitionLog(models.Model):
    """Optional model to store ASL recognition logs"""
    timestamp = models.DateTimeField(auto_now_add=True)
    predicted_char = models.CharField(max_length=10)
    confidence = models.FloatField()
    hand_detected = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.predicted_char} ({self.confidence:.2f}) at {self.timestamp}"


class GameScore(models.Model):
    """Model to store game scores for authenticated users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(default=300)  # Duration in seconds (default 5 minutes)
    game_mode = models.CharField(max_length=20, default='standard', choices=[('standard', 'Standard'), ('sprint', 'Short Word Sprint')])
    
    class Meta:
        ordering = ['-score', '-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.score} points ({self.game_mode}) on {self.created_at}"


class UserProfile(models.Model):
    """Extended user profile with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        help_text='Upload your profile picture'
    )
    bio = models.TextField(max_length=500, blank=True, help_text='Tell us about yourself')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_best_score(self):
        """Get the user's best score across all game modes"""
        best_score = GameScore.objects.filter(user=self.user).order_by('-score').first()
        return best_score.score if best_score else 0
    
    def get_profile_picture_url(self):
        """Get profile picture URL with fallback to default"""
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/images/default-profile.svg'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
