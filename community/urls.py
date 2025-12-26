from django.urls import path

from .views import *

urlpatterns = [
    path('communities/', communities_view, name='communities_view'),
    path('create_community/', create_community, name='create_community'),
    path('join_community/', join_community, name='join_community'),
    path('community/<int:community_id>/<int:family_id>/', community_detail, name='community_detail'),
    path('community/<int:community_id>/<int:family_id>/edit/', edit_community, name='edit_community'),
    path('community/<int:community_id>/<int:family_id>/chat/', chat_community, name='chat_community'),
    path('check-communityname/', check_communityname, name='check_communityname')
]