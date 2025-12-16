from rest_framework import serializers
from .models import UserErweitert, Level

class UserErweitertSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserErweitert
        fields = "__all__"

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = "__all__"