from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.friendships.views import ListCreateFriendshipView, ListPendingFriendshipView, FriendshipDetailView

urlpatterns = [
        path('users/<int:user_id>/friends', ListCreateFriendshipView.as_view(), name='user-friends'),
        path('users/<int:user_id>/friends/pending', ListPendingFriendshipView.as_view(), name='user-friends-pending'),
        path('friendships/<int:pk>', FriendshipDetailView.as_view(), name='friendship-detail') 
]
