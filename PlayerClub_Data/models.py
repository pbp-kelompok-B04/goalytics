from django.db import models

class Club(models.Model):
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    stadium = models.CharField(max_length=200, blank=True, null=True)  # 🏟️ nama stadion

    def __str__(self):
        return self.name

class Player(models.Model):
    external_id = models.IntegerField(unique=True, help_text="ID pemain dari dataset")
    name = models.CharField(max_length=200)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    position = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name




