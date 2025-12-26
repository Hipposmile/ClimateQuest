from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Personals
class Benachrichtigung(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    benachrichtigung = models.CharField(max_length=500)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.benachrichtigung} ({self.user})"