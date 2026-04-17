from django.urls import path

from .views import add, track_actions

urlpatterns = [
    path('add/', add, name='add'),
    path('track/', track_actions, name='track_actions'),
]