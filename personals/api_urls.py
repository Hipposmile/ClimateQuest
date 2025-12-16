from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import UserErweitertViewSet, LevelViewSet

router = DefaultRouter()
router.register(r'usererweitert', UserErweitertViewSet)
router.register(r'level', LevelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]