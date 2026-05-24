from django.contrib import admin
from .models import UserErweitert, Level, TreeCodes, IOSDevice


class UserErweitertAdmin(admin.ModelAdmin):
    filter_horizontal = ('planted_trees',)


admin.site.register(UserErweitert, UserErweitertAdmin)
admin.site.register(TreeCodes)
admin.site.register(IOSDevice)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('klimapunkte', 'description', 'description_en')
    ordering = ('klimapunkte',)
