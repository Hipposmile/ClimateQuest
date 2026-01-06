from django.contrib import admin
from .models import *

admin.site.register(Aktion)

@admin.register(AktionenListe)
class AktionenListeAdmin(admin.ModelAdmin):
    list_display = ("name", "klimapunkte", "mengeBeschreibung", "mengeBeschreibungSingular", "anmerkung")
    search_fields = ("name", "mengeBeschreibung", "anmerkung")
    list_filter = ("klimapunkte",)
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("actions",)  # bessere ManyToMany-Auswahl
