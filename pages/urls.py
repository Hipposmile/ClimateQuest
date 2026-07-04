from django.urls import path

from .views import mobile_apps, aknachhaltigkeit, pastel_done

urlpatterns = [
    path('mobile-apps/', mobile_apps, name='mobile_apps'),
    path('aknachhaltigkeit/', aknachhaltigkeit, name='aknachhaltigkeit'),
    path('pastel_done/', pastel_done, name='pastel_done'),
]
