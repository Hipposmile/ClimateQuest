from django.urls import path
from .views import *

urlpatterns = [
    path('artikel_overview/', artikel_overview, name='artikel_overview'),
    path('add_artikel/', add_artikel, name='add_artikel'),
    path('artikel_detail/<int:artikel_id>', artikel_detail, name='artikel_detail'),
    path('edit_artikel/<int:artikel_id>', edit_artikel, name='edit_artikel')
]