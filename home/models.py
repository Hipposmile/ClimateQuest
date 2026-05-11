from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.urls import reverse


# Personals
class Benachrichtigung(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    benachrichtigung_de = models.CharField(max_length=500)
    benachrichtigung_en = models.CharField(max_length=500)
    date = models.DateTimeField(default=timezone.now)
    url = models.URLField(max_length=500)

    def __str__(self):
        return f"{self.benachrichtigung_de} ({self.user})"

class ReportedUser(models.Model):
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reported_user")
    reporting_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="reporting_user")
    reason = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
