from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions, exceptions
from apps.friendships.models import Friendship
from apps.friendships.serializers import CreateFriendshipSerializer, ListFriendshipSerializer, FriendshipSerializer
from apps.users.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404

class ListCreateFriendshipView(ListCreateAPIView):
    ''' 
    List and create friendships.

    NOTE: All listed friendshps under this endpoint are ACCEPTED.
    '''
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ListFriendshipSerializer
        return CreateFriendshipSerializer

    def get_queryset(self):
        user = self.get_user_from_url()
        queryset = Friendship.objects.friendships_of_user(user)
        return queryset

    def create(self, request, *args, **kwargs):
        # Ensure the user exists
        user = self.get_user_from_url()
        # Ensure that the logged-in user is the one in the url
        if user != self.request.user:
            raise exceptions.PermissionDenied("You can only add friends to your own account")
        # Proceed with creation as normal
        return super().create(request, *args, **kwargs)
    
    def get_user_from_url(self):
        ''' 
        Gets the user associated with the user id within the URL.

        Returns:
            user (apps.users.models.User): The user associated with the URL.
        '''
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
        except User.DoesNotExist:
            raise exceptions.NotFound("User does not exist.")
        return user

class ListPendingFriendshipView(ListAPIView):
    ''' List incoming/outgoing friendships '''
    serializer_class = ListFriendshipSerializer
    permission_class = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = get_object_or_404(User.objects.all(), id=self.kwargs['user_id'])
        queryset = Friendship.objects.filter(
                Q(user1=user) | Q(user2=user), 
                status=Friendship.Status.PENDING
        ) 
        return queryset

class FriendshipDetailView(RetrieveUpdateDestroyAPIView):
    ''' View designated for managing specific friendships. '''
    queryset = Friendship.objects.all()
    serializer_class = FriendshipSerializer
    permission_class = [permissions.IsAuthenticated]
