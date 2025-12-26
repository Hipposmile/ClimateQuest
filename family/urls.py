from django.urls import path

from .views import *

urlpatterns = [
    # Families
    path('check-familyname/', check_familyname, name='check_familyname'),
    path('create_family/', create_family, name='create_family'),
    path('join_family/', join_family, name='join_family'),
    path('families/', families_view, name='families_view'),
    path('family/<int:family_id>/', family_detail, name='family_detail'),
    path('family/<int:family_id>/edit/', edit_family, name='edit_family'),
    path('family/<int:family_id>/chat/', chat_family, name='chat_family'),
]