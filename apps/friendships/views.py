from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions, exceptions
from apps.friendships.models import Friendship
from apps.friendships.serializers import FriendshipSerializer, AcceptedFriendshipSerializer, IncomingRequestSerializer, OutgoingRequestSerializer, CreateFriendshipSerializer
from apps.users.models import User
from apps.friendships.permissions import FriendshipContainsUser, IsRequestedUser, IsPendingFriendship, IsRecipientUser
from django.db.models import Q
from django.shortcuts import get_object_or_404

'''
Handles views for Friendships.

friendship.status == 'accepted' --> user1 and user2 are friends
friendship.status == 'pending' --> user1 sent a friend request to user2

Naming convention notes:
    'ListView' = collection/
    'DetailView' = collection/<collection_item>/
'''
class FriendshipListView(ListCreateAPIView):
    ''' 
    List and create friendships.

    NOTE: All listed friendshps under this endpoint are ACCEPTED.
    '''
    permission_classes = [(permissions.IsAuthenticated & IsRequestedUser) | permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AcceptedFriendshipSerializer
        return CreateFriendshipSerializer

    def get_queryset(self):
        user = get_object_or_404(User.objects.all(), id=self.kwargs['user_id'])
        queryset = Friendship.objects.friendships_of_user(user)
        return queryset

    def create(self, request, *args, **kwargs):
        # Get the user in the url and ensure the they exist
        user = get_object_or_404(User.objects.all(), id=self.kwargs['user_id'])
        # Ensure that the logged-in user is the one in the url
        if user != self.request.user:
            raise exceptions.PermissionDenied("You can only add friends to your own account")
        # Proceed with creation as normal
        return super().create(request, *args, **kwargs)
    
class IncomingFriendRequestView(ListAPIView):
    ''' List all incoming requests for the user in the url '''
    serializer_class = IncomingRequestSerializer
    permission_classes = [(permissions.IsAuthenticated & IsRequestedUser) | permissions.IsAdminUser]

    def get_queryset(self):
        user = get_object_or_404(User.objects.all(), id=self.kwargs['user_id'])
        queryset = Friendship.objects.incoming_requests_for_user(user)
        return queryset

class OutgoingFriendRequestView(ListAPIView):
    ''' List all outgoing requests for the user in the url '''
    serializer_class = OutgoingRequestSerializer
    permission_classes = [(permissions.IsAuthenticated & IsRequestedUser) | permissions.IsAdminUser]

    def get_queryset(self):
        user = get_object_or_404(User.objects.all(), id=self.kwargs['user_id'])
        queryset = Friendship.objects.outgoing_requests_for_user(user)
        return queryset

class FriendshipDetailView(RetrieveUpdateDestroyAPIView):
    ''' View designated for managing specific friendships. '''
    queryset = Friendship.objects.all()
    serializer_class = FriendshipSerializer

    # Disable PUT since we only want to be able to change status
    http_method_names = ['get', 'patch', 'delete']

    def get_permissions(self):
        # A user can retrieve and destroy a friendship if they belong to it or they are an admin.
        permission_classes = [(permissions.IsAuthenticated & FriendshipContainsUser) | permissions.IsAdminUser]
        # A user can update the status of a friendship (accept it) if they are the recipient or admin.
        if self.request.method == 'PATCH':
            permission_classes = [((permissions.IsAuthenticated & IsRecipientUser) | permissions.IsAdminUser) & IsPendingFriendship]
        return [permission() for permission in permission_classes]

