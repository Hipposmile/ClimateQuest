from rest_framework import serializers
from .models import Answer, Comment, Artikel

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"

class ArtikelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artikel
        fields = "__all__"