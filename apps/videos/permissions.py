from rest_framework.permissions import BasePermission

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
        if obj.is_public:
            return True
        #TODO: making it here means video is private, so check the shared table
        return True
