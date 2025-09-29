from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from django.utils import timezone
from datetime import timedelta

# Verbrauch 
class AktionenListe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    klimapunkte = models.FloatField()
    mengeBeschreibung = models.CharField(max_length=200)
    anmerkung = models.CharField(max_length=500)
    source = models.CharField(max_length=1000)

    def __str__(self):
        return self.name

class Aktion(models.Model):
    description = models.CharField(max_length=500, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.FloatField()
    aktion = models.ForeignKey(AktionenListe, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    @property
    def impact(self):
        return self.quantity * self.aktion.klimapunkte

    def __str__(self):
        return f"{self.aktion.name} ({self.user})"


    def __str__(self):
        return self.description