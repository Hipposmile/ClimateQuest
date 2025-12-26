from django.urls import path

from .views import *

urlpatterns = [
    path('klimapunkte/<int:user_id>', klimapunkte_view, name='klimapunkte_view'),
path('klimapunkte/me', klimapunkte_me, name='klimapunkte_me'),
    path('level/<int:user_id>', level_view, name='level_view'),
    path('level/me', level_me, name='level_me'),
    path('overview/', users_overview, name='users_overview'),
    path('detail/<int:user_id>', user_detail, name='user_detail')
]