from django.urls import path
from .views import *


urlpatterns = [
    path('', presents_overview, name='presents_overview'),
    path('add_present/', add_present, name='add_present'),
    path('present_detail/<uuid:present_secret_key>/', present_detail, name='present_detail'),
    path('present/<uuid:present_secret_key>/delete/', delete_present, name='delete_present'),
]
