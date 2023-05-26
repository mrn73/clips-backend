from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.parsers import JSONParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions
from apps.videos.models import Video
from apps.videos.serializers import VideoReadSerializer, VideoWriteSerializer
from apps.videos.permissions import IsCreator, IsShared
from apps.users.models import User

'''
Eventually add a feed which can be used as homepage.
class FeedView(ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter the listed videos to videos the user can see if the user is not
        # a staff member
        if not (user.is_authenticated and user.is_staff):
            # Include all public videos by default
            queryset = Video.objects.filter(is_public=True)
            if user.is_authenticated:
                #TODO: also add videos that are shared with the user
                queryset |= Video.objects.filter(creator=user)

        return queryset
    
    def perform_destroy(self, instance):
        instance.video.delete(False)
        instance.delete()
'''

class VideoListView(ListCreateAPIView):
    '''
    View to list or post videos. Listing videos only shows their metadata, not the actual video.
    '''
    def get_serializer_class(self):
        serializer_class = VideoReadSerializer
        if self.request.method == 'POST':
            serializer_class = VideoWriteSerializer
        return serializer_class

    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'POST':
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        ''' 
        Override this function to add 'is_list' key into the context 
        dictionary. In the serializer, if 'is_list' is true, then we won't
        list the shared users in the serialized output.
        '''
        context = super().get_serializer_context()
        if self.request.method == 'GET':
            context['is_list'] = True
        return context

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        requester = self.request.user

        # Video visibility depends on the requested user:
        #   -admin: sees all of a user's videos
        #   -user: if the creator, sees all videos; else, sees only the videos
        #          of a user that is public or shared with them
        #   -anonymous: sees only a user's public videos
        if requester.is_authenticated:
            if requester.is_staff:
                return Video.objects.filter(creator=user)
            return Video.objects.filter(
                Q(creator=user) & 
                (Q(is_public=True) | Q(shared_with__user=requester) | Q(creator=requester))
            )
        return Video.objects.filter(Q(creator=user) & Q(is_public=True))

class VideoDetailView(RetrieveUpdateDestroyAPIView):
    '''
    View to retrieve / update / delete video instances, including the video file
    and metadata.
    '''
    queryset = Video.objects.all()
    # Disables PUT
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        serializer_class = VideoWriteSerializer
        if self.request.method == 'GET':
            serializer_class = VideoReadSerializer
        return serializer_class

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [((permissions.IsAuthenticated & IsCreator) | IsShared) | permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated & (IsCreator | permissions.IsAdminUser)]
        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        instance.video.delete(False)
        instance.delete()
