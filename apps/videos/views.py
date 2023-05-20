from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.parsers import JSONParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions
from apps.videos.models import Video
from apps.videos.serializers import VideoSerializer
from apps.videos.permissions import IsCreator, IsShared
from apps.users.models import User

class VideoViewSet(ModelViewSet):
    '''
    THIS VIEW IS UNUSED!
        - Will use it to make the "feed" view.
    '''
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

class VideoListView(ListCreateAPIView):
    '''
    View to list or post videos. Listing videos only shows their metadata, not the actual video.
    '''
    serializer_class = VideoSerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'POST':
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        # TODO: Filter also by shared (and note admins can see all videos)
        return Video.objects.filter(
                Q(creator=user) | Q(is_public=True) 
        )

class VideoDetailView(RetrieveUpdateDestroyAPIView):
    '''
    View to retrieve / update / delete video instances, including the video file and metadata.
    '''
    serializer_class = VideoSerializer
    queryset = Video.objects.all()
    # Disables PUT
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [((permissions.IsAuthenticated & IsCreator) | IsShared) | permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated & (IsCreator | permissions.IsAdminUser)]
        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        instance.video.delete(False)
        instance.delete()
