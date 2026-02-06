from django.contrib.auth.models import User
from django.db import models
from core.validators import validate_image


# Create your models here.
class Update(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Petition(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    img = models.ImageField(upload_to='petitions/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    signs = models.ManyToManyField(User, blank=True, null=True, related_name='petition_sign')
    update = models.ForeignKey(Update, on_delete=models.CASCADE, related_name='petition_update', blank=True,
                               validators=[validate_image])
