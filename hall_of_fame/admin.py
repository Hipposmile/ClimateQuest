from django.contrib import admin

from hall_of_fame.models import HallOfFameEntry, HallOfFameData

# Register your models here.
admin.site.register(HallOfFameEntry)
admin.site.register(HallOfFameData)
