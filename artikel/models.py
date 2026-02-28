from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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
    name = models.CharField(max_length=100)
    content = models.TextField()
    comments = models.ManyToManyField(Comment, related_name='artikel', blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    like = models.ManyToManyField(User, blank=True, related_name='artikel_like')
    date_time = models.DateField(auto_now=True)
    verified = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    msg_if_wrong = models.CharField(max_length=100, blank=True, null=True, default=None)

    def clean(self):
        if self.verified and self.msg_if_wrong:
            raise ValidationError({
                'verified': 'verified darf nur True sein, wenn msg_if_wrong leer ist.',
                'msg_if_wrong': 'msg_if_wrong muss leer sein, wenn verified True ist.'
            })

    def like_count(self):
        return self.like.count()

    def __str__(self):
        return self.name
