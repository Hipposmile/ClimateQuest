from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Families
class Family(models.Model):
    name = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    admin_password = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='families')
    chat = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Nur hashen, wenn das Passwort nicht schon gehashed ist
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        if not self.admin_password.startswith('pbkdf2_'):
            self.admin_password = make_password(self.admin_password)
        super().save(*args, **kwargs)

    def member_count(self):
        return self.members.count()

class FamilyChatMessage(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    message = models.TextField()
    erstellt_am = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message