from django.contrib import admin

from .models import Answer, Category, ForumPost

# Register your models here.
admin.site.register(ForumPost)
admin.site.register(Answer)
admin.site.register(Category)
