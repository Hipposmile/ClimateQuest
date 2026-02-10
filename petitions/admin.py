from django.contrib import admin
from django.utils.html import format_html

from petitions.models import Category
from .models import Petition


@admin.register(Petition)
class PetitionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'creator',
        'category',
        'created_at',
        'sign_count',
    )
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'content', 'creator__username')
    readonly_fields = ('created_at', 'image_preview')
    filter_horizontal = ('signs', 'updates', 'comments')
    ordering = ('-created_at',)

    def sign_count(self, obj):
        return obj.signs.count()

    sign_count.short_description = "Signatures"

    def image_preview(self, obj):
        if obj.img:
            return format_html(
                '<img src="{}" style="max-height: 120px; border-radius: 4px;" />',
                obj.img.url
            )
        return "—"

    image_preview.short_description = "Image Preview"


admin.site.register(Category)
