from django.contrib import admin
from .models import Family, FamilyChatMessage

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'member_count')
    filter_horizontal = ('members',)

@admin.register(FamilyChatMessage)
class FamilyChatMessageAdmin(admin.ModelAdmin):
    list_display = ('family', 'user', 'message', 'erstellt_am')
    list_filter = ('family', 'user')
    search_fields = ('message',)
