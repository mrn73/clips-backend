from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from apps.videos.models import Video
from apps.videos.serializers import VideoSerializer

class VideoViewSet(ModelViewSet):
    serializer_class = VideoSerializer

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]
        if self.action not in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        # include all public videos by default
        queryset = Video.objects.filter(is_public=True)
        if user.is_authenticated:
            # admins can see all videos
            if user.is_staff:
                return Video.objects.all()
            queryset |= Video.objects.filter(creator=user)
        return queryset
    
    def perform_destroy(self, instance):
        instance.video.delete(False)
        instance.delete()
