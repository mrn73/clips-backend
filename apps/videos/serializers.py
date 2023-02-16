from rest_framework import serializers
from apps.videos.models import Video
from django.core.files.storage import FileSystemStorage

class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        exclude = ['creator_id', 'uploaded_at']

class VideoLoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'video_name', 'description', 'uploaded_at']
