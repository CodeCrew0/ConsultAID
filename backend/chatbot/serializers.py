from rest_framework import serializers
from .models import Document, ChatLog

class ChatQuerySerializer(serializers.Serializer):
    query = serializers.CharField(max_length=1000)
    session_id = serializers.CharField(max_length=100, required=False)

class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    language = serializers.CharField()
    confidence = serializers.FloatField()
    session_id = serializers.CharField()

class DocumentUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    file = serializers.FileField()

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class ChatLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatLog
        fields = '__all__'