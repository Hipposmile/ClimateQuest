from django.urls import path
from .views import *

urlpatterns = [
    path('add_petition/', add_petition, name='add_petition'),
]
