from django.contrib import admin

from petitions.models import Category

from .models import Petition


@admin.register(Petition)
class PetitionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "creator",
        "category",
        "created_at",
        "sign_count",
    )
    list_filter = ("category", "created_at")
    search_fields = ("title", "content", "creator__username")
    readonly_fields = ("created_at",)
    filter_horizontal = ("signs", "updates", "comments")
    ordering = ("-created_at",)

    def sign_count(self, obj):
        return obj.signs.count()

    sign_count.short_description = "Signatures"


admin.site.register(Category)
