from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('basic', 'Basic User'),
        ('analyst', 'Analyst'),
    ]

    LEAGUE_CHOICES = [
        ('EPL', 'English Premier League'),
        ('LALIGA', 'La Liga'),
        ('SERIEA', 'Serie A'),
        ('BUNDESLIGA', 'Bundesliga'),
        ('LIGUE1', 'Ligue 1'),
        ('OTHER', 'Other'),
    ]

    POSITION_CHOICES = [
        ('FW', 'Forward'),
        ('MF', 'Midfielder'),
        ('DF', 'Defender'),
        ('GK', 'Goalkeeper'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='basic')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    favorite_team = models.ForeignKey('PlayerClub_Data.Club', on_delete=models.SET_NULL, null=True, blank=True, related_name='fans')
    instagram_url = models.URLField(blank=True, null=True)
    x_url = models.URLField(blank=True, null=True, help_text="Link ke profil X (Twitter)")
    website_url = models.URLField(blank=True, null=True)
    favorite_league = models.CharField(max_length=20, choices=LEAGUE_CHOICES, blank=True, null=True)
    preferred_position = models.CharField(max_length=20, choices=POSITION_CHOICES, blank=True, null=True)
    

    def __str__(self):
        return f"{self.user.username} ({self.role})"
