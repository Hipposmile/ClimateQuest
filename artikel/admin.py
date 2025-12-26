from django.contrib import admin

from .models import *


class ArtikelAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_time', 'creator')
    filter_horizontal = ('comments',)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment',)
    filter_horizontal = ('answers',)

admin.site.register(Artikel, ArtikelAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Answer)