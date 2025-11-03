from django.db import models
from django.contrib.auth.models import User
import uuid
# Create your models here.
class Congratulation(models.Model):
    message = models.TextField()
    congratulator = models.CharField(max_length=100)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.message
    
class Present(models.Model):
    recipient = models.CharField(max_length=100)
    congratulations = models.ManyToManyField(Congratulation, related_name='presents')
    candles = models.IntegerField(default=0)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    secret_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    @property
    def congratulation_count(self):
        return self.congratulations.count()
    
    def __str__(self):
        return f"Present for {self.recipient}"