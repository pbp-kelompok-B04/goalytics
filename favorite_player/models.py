from django.db import models
from django.contrib.auth.models import User
from PlayerClub_Data.models import Player

# Create your models here.
class FavoritePlayer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.player.name}"