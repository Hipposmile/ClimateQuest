from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User 

# Create your models here.
class Answer(models.Model):
    answer = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artikel_answer')
    date_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer

class Comment(models.Model):
    comment = models.TextField()
    answers = models.ManyToManyField(Answer, related_name='comment', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artikel_comment')
    date_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.comment
    
class Artikel(models.Model):
    name = models.CharField(max_length=200)
    content = models.TextField()
    comments = models.ManyToManyField(Comment, related_name='artikel', blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    like = models.ManyToManyField(User, blank=True, related_name='artikel_like')
    date_time = models.DateTimeField(auto_now=True)

    def like_count(self):
        return self.like.count()

    def __str__(self):
        return self.name