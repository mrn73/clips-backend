from django.urls import path, include, reverse
from rest_framework.routers import DefaultRouter
from apps.friendships.views import FriendshipListView, FriendshipDetailView, IncomingFriendRequestView, OutgoingFriendRequestView

urlpatterns = [
        path('users/<int:user_id>/friends', FriendshipListView.as_view(), name='user-friends'),
        path('users/<int:user_id>/friends/incoming-requests', IncomingFriendRequestView.as_view(), name='user-friends-incoming'),
        path('users/<int:user_id>/friends/outgoing-requests', OutgoingFriendRequestView.as_view(), name='user-friends-outgoing'),
        path('friendships/<int:pk>', FriendshipDetailView.as_view(), name='friendship-detail') 
]
