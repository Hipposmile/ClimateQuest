from django.contrib import admin

from .models import Answer, Artikel, Category, Comment


class ArtikelAdmin(admin.ModelAdmin):
    list_display = ("name_de", "name_en", "updated_at", "creator")
    filter_horizontal = ("comments",)


class CommentAdmin(admin.ModelAdmin):
    list_display = ("comment",)
    filter_horizontal = ("answers",)


admin.site.register(Artikel, ArtikelAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Answer)
admin.site.register(Category)
