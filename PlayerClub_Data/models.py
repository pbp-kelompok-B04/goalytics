from django.db import models

class Club(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    stadium = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class Player(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    position = models.CharField(max_length=50, choices=[
        ('GK', 'Goalkeeper'),
        ('DEF', 'Defender'),
        ('MID', 'Midfielder'),
        ('FWD', 'Forward'),
    ])

    def __str__(self):
        return self.name

class Goalkeeper(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='goalkeeper_stats')
    saves = models.PositiveIntegerField(default=0)
    clean_sheets = models.PositiveIntegerField(default=0)
    penalty_saves = models.PositiveIntegerField(default=0)


class Defender(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='defender_stats')
    tackles = models.PositiveIntegerField(default=0)
    interceptions = models.PositiveIntegerField(default=0)
    clearances = models.PositiveIntegerField(default=0)


class Midfielder(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='midfielder_stats')
    passes_completed = models.PositiveIntegerField(default=0)
    chances_created = models.PositiveIntegerField(default=0)


class Forward(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='forward_stats')
    shots_on_target = models.PositiveIntegerField(default=0)
    dribbles_completed = models.PositiveIntegerField(default=0)
