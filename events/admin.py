from django.contrib import admin
from .models import Event, Question, Answer
from django.contrib.auth.models import User

class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_time', 'creator')
    filter_horizontal = ('participants', 'questions')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question',)
    filter_horizontal = ('answers',)

admin.site.register(Event, EventAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)