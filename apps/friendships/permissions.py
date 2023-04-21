from rest_framework.permissions import BasePermission
from apps.friendships.models import Friendship

class FriendshipContainsUser(BasePermission):
    ''' Checks if a friendship object contains the user making the request. '''
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return request.user == obj.user1 or request.user == obj.user2

class IsRequestedUser(BasePermission):
    ''' Checks if the user in the url is the user making the request. '''
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.id == view.kwargs['user_id']

class IsPendingFriendship(BasePermission):
    ''' Checks if a friendship's status is pending. If not, the status can't be changed. '''
    message = "You may not PUT/PATCH an accepted request. Call DELETE to remove a friend."

    def has_object_permission(self, request, view, obj):
        return obj.status == Friendship.Status.PENDING

class IsRecipientUser(BasePermission):
    ''' 
    Checks if the user making the request is the recipient of the friend request.
    Ensures that the user who sent the request can't accept it on behalf of the receiver.
    '''
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return obj.user2 == request.user

