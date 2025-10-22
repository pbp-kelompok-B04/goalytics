from django.db import models

class Club(models.Model):
    name = models.CharField(max_length=200, unique=True)
    league = models.CharField(max_length=100)
    season = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} ({self.league})"


class Player(models.Model):
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DF', 'Defender'),
        ('MF', 'Midfielder'),
        ('FW', 'Forward'),
    ]

    name = models.CharField(max_length=200)
    nation = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=50, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    born = models.PositiveIntegerField(blank=True, null=True)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, related_name='players')
    
    #stat umum
    goals = models.FloatField(default=0)
    assists = models.FloatField(default=0)
    xg = models.FloatField(default=0)
    npxg = models.FloatField(default=0)
    xag = models.FloatField(default=0)

    #stats progresi
    Progressive_Carries = models.FloatField(default=0)
    Progressive_Passes = models.FloatField(default=0)
    Progressive_Receptions = models.FloatField(default=0)

    #stats passing
    passes_completed = models.PositiveIntegerField(default=0)
    passes_attempted = models.PositiveIntegerField(default=0)
    pass_accuracy = models.FloatField(blank=True, null=True)

    # stats bertahan
    tackles = models.PositiveIntegerField(default=0)
    tackles_won = models.PositiveIntegerField(default=0)
    challenges_won = models.PositiveIntegerField(default=0)
    challenges_attempted = models.PositiveIntegerField(default=0)
    blocks = models.PositiveIntegerField(default=0)
    clearances = models.PositiveIntegerField(default=0)

    #stats khusus kiper
    saves = models.PositiveIntegerField(blank=True, null=True)
    save_percentage = models.FloatField(blank=True, null=True)
    clean_sheets = models.PositiveIntegerField(blank=True, null=True)
    clean_sheet_percentage = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.position})"
