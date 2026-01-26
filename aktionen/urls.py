from django.urls import path

from .views import *

urlpatterns = [
    path('add/', add, name='add'),
    path('edit/<int:action_id>/', edit_action, name='edit_action'),
]