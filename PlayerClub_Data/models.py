from django.db import models

class Club(models.Model):
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    stadium = models.CharField(max_length=200, blank=True, null=True)  # 🏟️ nama stadion

    def __str__(self):
        return self.name





