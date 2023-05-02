from rest_framework.permissions import BasePermission

class IsRequestedUser(BasePermission):
    ''' Checks if the user in the url is the user making the request. '''
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.id == view.kwargs['user_id']

class IsCreator(BasePermission):
    ''' Checks that the private group creator is the user in the request '''
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return obj.creator == request.user
