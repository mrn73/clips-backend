from rest_framework.permissions import BasePermission
from apps.videos.models import Shared

class IsCreator(BasePermission):
    ''' 
    Permission class ran on video objects to see if the user
    in the request is the creator of the video. 
    '''
    def has_object_permission(self, request, view, obj):
        return request.user == obj.creator

class IsShared(BasePermission):
    '''
    Permission class ran on video objects to see if the video
    is shared with the user in the request.
    '''
    def has_object_permission(self, request, view, obj):
        if obj.is_public or (
                request.user.is_authenticated and 
                Shared.objects.filter(video=obj, user=request.user).exists()
        ):
            return True
        return False
        
