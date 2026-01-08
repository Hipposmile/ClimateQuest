from django.urls import path
from .views import *
urlpatterns = [
    path('testers/', testers, name='testers'),
]