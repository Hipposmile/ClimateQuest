from django.contrib import admin
from .models import Aktion, AktionenListe, Category, TrackedActions

admin.site.register(Aktion)
admin.site.register(TrackedActions)

@admin.register(AktionenListe)
class AktionenListeAdmin(admin.ModelAdmin):
    list_display = ("name", "klimapunkte", "mengeBeschreibung", "anmerkung", "max")
    search_fields = ("name", "mengeBeschreibung", "anmerkung")
    list_filter = ("klimapunkte",)
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("actions",)
