from django.contrib import admin
from .models import Benachrichtigung, ReportedUser

admin.site.register(Benachrichtigung)

@admin.register(ReportedUser)
class ReportedUserAdmin(admin.ModelAdmin):
    list_display = ("reported_user", "reporting_user", "reason", "reviewed", "date")
    list_filter = ("reviewed", "date")
    search_fields = ("reported_user__username", "reporting_user__username", "reason")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if "reviewed__exact" not in request.GET:
            return qs.filter(reviewed=False)
        return qs
