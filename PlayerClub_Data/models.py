from django.db import models
# sementara gini dulu aja, nanti ditambah lagi
class Club(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    stadium = models.CharField(max_length=200, blank=True, null=True)  

    def __str__(self):
        return self.name

class Player(models.Model):
    id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    position = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    height_cm = models.FloatField(blank=True, null=True)
    total_goals = models.PositiveIntegerField(default=0)
    total_assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    total_win = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name