from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Create your models here.
class Update(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Category(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Answer(models.Model):
    answer = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='petition_answer')
    date_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer


class Comment(models.Model):
    comment = models.TextField()
    answers = models.ManyToManyField(Answer, related_name='comment', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='petition_comment')
    date_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.comment


class Petition(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    goal = models.IntegerField()
    created_at = models.DateField(auto_now_add=True)
    signs = models.ManyToManyField(User, blank=True, related_name='petition_sign')
    updates = models.ManyToManyField(Update, related_name='petition_update', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='petition_category')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_petitions')
    comments = models.ManyToManyField(Comment, related_name='petition_comment', blank=True)
    success = models.BooleanField(default=False)

    def signs_count(self):
        return self.signs.count()

    def __str__(self):
        return self.title
