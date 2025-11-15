from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from django.utils import timezone
from datetime import timedelta

class UserErweitert(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    mailinglist = models.BooleanField(default=True)
    mail_verified = models.BooleanField(default=False)
    statement = models.TextField(default="Hallo. Ich benutze ClimateQuest.")

    def __str__(self):
        return self.user.username

# Wichtig: Immer auch ein Level ab 0 Punkten haben, sonst kommt es zu Fehlern
class Level(models.Model):
    klimapunkte = models.IntegerField()
    description = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.description} ({self.klimapunkte})'