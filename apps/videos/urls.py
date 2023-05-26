from django.urls import path, include
from apps.videos.views import VideoListView, VideoDetailView
from rest_framework.routers import DefaultRouter

urlpatterns = [
        path('users/<int:user_id>/videos/', 
             VideoListView.as_view(),
             name='user-videos'
        ),
        path('videos/<int:pk>/', 
             VideoDetailView.as_view(),
             name='video-detail'
        ),
]
