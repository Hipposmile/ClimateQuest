from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class HallOfFameEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hall_of_fame_entry')
    description_de = models.TextField()
    description_en = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} --> {self.description_de}"
