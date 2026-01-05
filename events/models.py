from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Answer(models.Model):
    answer = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_answer')
    date_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer

class Question(models.Model):
    question = models.TextField()
    answers = models.ManyToManyField(Answer, related_name='question', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_question')
    date_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question

class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    adress = models.CharField(max_length=100)
    date_time = models.DateTimeField()
    duration = models.FloatField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='events')
    questions = models.ManyToManyField(Question, related_name='event', blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    @property
    def participants_count(self):
        return self.participants.count()

    def __str__(self):
        return self.name
