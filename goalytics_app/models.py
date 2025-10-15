from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    THEME_CHOICES = [("light", "Light"), ("dark", "Dark")]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_league = models.CharField(max_length=100, blank=True)
    favorite_club = models.CharField(max_length=100, blank=True)
    display_mode = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"