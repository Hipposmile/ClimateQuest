from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AnswerViewSet, CommentViewSet, ArtikelViewSet

router = DefaultRouter()
router.register(r'posts', AnswerViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'articles', ArtikelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]