from rest_framework import viewsets
from .models import UserErweitert, Level
from .serializers import UserErweitertSerializer, LevelSerializer

class UserErweitertViewSet(viewsets.ModelViewSet):
    queryset = UserErweitert.objects.all()
    serializer_class = UserErweitertSerializer

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer