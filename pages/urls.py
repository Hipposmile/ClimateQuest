from django.urls import path

from .views import mobile_apps, aknachhaltigkeit

urlpatterns = [
    path('mobile-apps/', mobile_apps, name='mobile_apps'),
    path('aknachhaltigkeit/', aknachhaltigkeit, name='aknachhaltigkeit')
]
