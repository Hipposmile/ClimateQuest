from django.urls import path

from .views import add

urlpatterns = [
    path('add/', add, name='add'),
]