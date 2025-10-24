from django.db import models
from django.contrib.auth.models import User
from PlayerClub_Data.models import Player

class SavedComparison(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    player1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='comparisons_as_player1')
    player2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='comparisons_as_player2')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'player1', 'player2']
    
    def __str__(self):
        return f"{self.player1.name} vs {self.player2.name} - {self.user.username}"

# Create your models here.
