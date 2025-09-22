from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('klimapunkte/<int:user_id>', klimapunkte_view, name='klimapunkte_view'),
    path('level/<int:user_id>', level_view, name='level_view'),
]