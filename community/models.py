from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

from django.utils import timezone

from family.models import Family

class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    admin_password = models.CharField(max_length=100)
    members = models.ManyToManyField(Family, related_name='communities', blank=True)
    chat = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        if not self.admin_password.startswith('pbkdf2_'):
            self.admin_password = make_password(self.admin_password)
        super().save(*args, **kwargs)

    def members_count(self):
        return self.members.count()
    
    def user_members(self):
        return User.objects.filter(families__in=self.members.all()).distinct()

class CommunityChatMessage(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    message = models.TextField()
    erstellt_am = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message