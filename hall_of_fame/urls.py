from django.urls import path

import hall_of_fame
from .views import intro, hall_of_fame_detail

urlpatterns = [
    path('', intro, name='intro'),
    path('hall_of_fame/', hall_of_fame_detail, name='hall_of_fame_detail'),
]