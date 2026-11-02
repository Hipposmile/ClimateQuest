from django.urls import path

from .views import (
    action_detail,
    history,
    history_me,
    klimapunkte_me,
    klimapunkte_view,
    level_me,
    level_view,
    user_detail,
    users_overview,
)

urlpatterns = [
    path("klimapunkte/<int:user_id>/", klimapunkte_view, name="klimapunkte_view"),
    path("klimapunkte/me/", klimapunkte_me, name="klimapunkte_me"),
    path("level/<int:user_id>/", level_view, name="level_view"),
    path("level/me/", level_me, name="level_me"),
    path("history/<int:user_id>/", history, name="history"),
    path("action_detail/<int:action_id>/<int:user_id>/", action_detail, name="action_detail"),
    path("history/me/", history_me, name="history_me"),
    path("overview/", users_overview, name="users_overview"),
    path("detail/<int:user_id>/", user_detail, name="user_detail"),
]
