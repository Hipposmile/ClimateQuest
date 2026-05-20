from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Create your models here.
class HallOfFameEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hall_of_fame_entry')
    description_de = models.TextField()
    description_en = models.TextField()
    created_at = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} --> {self.description_de}"
