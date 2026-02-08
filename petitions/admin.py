from django.contrib import admin

from petitions.models import Petition, Category

# Register your models here.
admin.site.register(Petition)
admin.site.register(Category)