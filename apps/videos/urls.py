from django.urls import path, include
from apps.videos.views import VideoViewSet, VideoListView, VideoDetailView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')
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
