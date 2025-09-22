from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class ForumPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_time = models.DateTimeField(default=timezone.now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Answer(models.Model):
    content = models.TextField()
    date_time = models.DateTimeField(default=timezone.now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    forum_post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='answers')

    def __str__(self):
        return f"Antwort von {self.creator} auf {self.forum_post.title}"