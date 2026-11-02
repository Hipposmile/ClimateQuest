from django.urls import path

from .views import aknachhaltigkeit, mobile_apps, pastel_done

urlpatterns = [
    path("mobile-apps/", mobile_apps, name="mobile_apps"),
    path("aknachhaltigkeit/", aknachhaltigkeit, name="aknachhaltigkeit"),
    path("pastel_done/", pastel_done, name="pastel_done"),
]
