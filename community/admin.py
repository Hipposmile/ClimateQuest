from django.contrib import admin
from .models import Community, CommunityChatMessage

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'members_count')
    filter_horizontal = ('members',)
admin.site.register(CommunityChatMessage)