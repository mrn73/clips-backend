from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from apps.videos.models import Video
from apps.videos.serializers import VideoSerializer
from apps.videos.permissions import IsCreator, IsShared

class VideoViewSet(ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    # Disables PUT
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [permissions.AllowAny]
        elif self.action == 'retrieve':
            permission_classes = [((permissions.IsAuthenticated & IsCreator) | IsShared) | permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated & (IsCreator | permissions.IsAdminUser)]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter the listed videos to videos the user can see if the user is not a staff member
        if self.action == 'list' and not (user.is_authenticated and user.is_staff):
            # Include all public videos by default
            queryset = Video.objects.filter(is_public=True)
            if user.is_authenticated:
                #TODO: also add videos that are shared with the user
                queryset |= Video.objects.filter(creator=user)

        return queryset
    
    def perform_destroy(self, instance):
        instance.video.delete(False)
        instance.delete()
