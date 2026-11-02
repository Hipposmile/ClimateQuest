from django.contrib import admin

from hall_of_fame.models import HallOfFameData, HallOfFameEntry

# Register your models here.
admin.site.register(HallOfFameEntry)
admin.site.register(HallOfFameData)
