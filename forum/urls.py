from django.urls import path
from .views import *

urlpatterns = [
    path('forum_overview/', forum_overview, name='forum_overview'),
    path('add_forum_post/', add_forum_post, name='add_forum_post'),
    path('post_detail/<int:post_id>/', post_detail, name='post_detail')
]