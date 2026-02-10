from django.urls import path
from .views import *

urlpatterns = [
    path('add_petition/', add_petition, name='add_petition'),
    path('petition_detail/<int:petition_id>/', petition_detail, name='petition_detail'),
    path('petitions_overview/', petitions_overview, name='petitions_overview'),
    path('update_petition/<int:petition_id>/', update_petition, name='update_petition'),
]
