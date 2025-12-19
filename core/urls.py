from django.urls import path, include
from .views import home, send_push

urlpatterns = [
    path('', home),
]
