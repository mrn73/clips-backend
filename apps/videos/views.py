from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.viewsets import ModelViewSet
from apps.videos.models import Video
from apps.videos.serializers import VideoUploadSerializer, VideoLoadSerializer
import datetime
from django.utils import timezone

class VideoViewSet(ModelViewSet):
    queryset = Video.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return VideoLoadSerializer
        return VideoUploadSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_at=datetime.datetime.now(tz=timezone.utc))

    def perform_destroy(self, instance):
        instance.video.delete(False)
        instance.delete()

