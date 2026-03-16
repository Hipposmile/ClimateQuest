from django.contrib import admin
from .models import UserErweitert, Level, TreeCodes

class UserErweitertAdmin(admin.ModelAdmin):
    filter_horizontal = ('planted_trees',)

admin.site.register(UserErweitert, UserErweitertAdmin)
admin.site.register(Level)
admin.site.register(TreeCodes)
