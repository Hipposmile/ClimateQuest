from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from django.utils import timezone
from datetime import timedelta

# Verbrauch 
class AktionenListe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    klimapunkte = models.FloatField()
    mengeBeschreibung = models.CharField(max_length=200, null=True, blank=True)
    anmerkung = models.CharField(max_length=500, blank=True, null=True)
    date = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Aktion(models.Model):
    description = models.CharField(max_length=500, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.FloatField(null=True)
    aktion = models.ForeignKey(AktionenListe, on_delete=models.CASCADE, null=True)
    date = models.DateField(default=timezone.now, null=True)
    
    @property
    def impact(self):
        if self.aktion.date:
            return self.quantity * self.aktion.klimapunkte
        else:
            return self.aktion.klimapunkte

    def __str__(self):
        return f"{self.aktion.name} ({self.user})"


    def __str__(self):
        return self.description