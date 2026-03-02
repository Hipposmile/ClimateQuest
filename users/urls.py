from django.urls import path

from .views import klimapunkte_view, klimapunkte_me, level_view, level_me, history, history_me, users_overview, user_detail

urlpatterns = [
    path('klimapunkte/<int:user_id>', klimapunkte_view, name='klimapunkte_view'),
path('klimapunkte/me', klimapunkte_me, name='klimapunkte_me'),
    path('level/<int:user_id>', level_view, name='level_view'),
    path('level/me', level_me, name='level_me'),
    path('history/<int:user_id>', history, name='history'),
    path('history/me', history_me, name='history_me'),
    path('overview/', users_overview, name='users_overview'),
    path('detail/<int:user_id>', user_detail, name='user_detail')
]