from django.urls import path

from .views import *

urlpatterns = [
    # Verbrauch
    path('add/', add, name='add'),
    path('history/', history, name='history'),
    path('edit/<int:action_id>/', edit_action, name='edit_action'),
]