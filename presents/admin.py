from django.contrib import admin
from .models import Present, Congratulation


@admin.register(Present)
class PresentAdmin(admin.ModelAdmin):
    list_display = (
        'recipient',
        'creator',
        'candles',
        'congratulation_count',
        'created_at',
        'secret_key_short',
    )
    list_filter = ('created_at', 'creator')
    search_fields = ('recipient', 'creator__username')
    readonly_fields = ('created_at', 'secret_key')
    filter_horizontal = ('congratulations',)

    def secret_key_short(self, obj):
        return str(obj.secret_key)[:8] + "..."

    secret_key_short.short_description = "Secret Key"


admin.site.register(Congratulation)
