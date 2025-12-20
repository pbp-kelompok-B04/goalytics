# models.py
from django.db import models
from django.contrib.auth.models import User
from PlayerClub_Data.models import Player

class DreamSquad(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dream_squads')
    name = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def player_count(self):
        return self.players.count()

class DreamSquadPlayer(models.Model):
    squad = models.ForeignKey(DreamSquad, on_delete=models.CASCADE, related_name='players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='in_dream_squads')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('squad', 'player')
        ordering = ('added_at',)

    def __str__(self):
        return f"{self.player.name} in {self.squad.name}"

class BannedWord(models.Model):
    word = models.CharField(max_length=50, unique=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word