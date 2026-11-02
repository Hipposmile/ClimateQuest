from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from core.models import HashPasswordsOnSaveMixin


# Families
class Family(HashPasswordsOnSaveMixin, models.Model):
    name = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    admin_password = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name="families", blank=True)
    chat = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def member_count(self):
        return self.members.count()


class FamilyChatMessage(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    message = models.TextField()
    erstellt_am = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message
