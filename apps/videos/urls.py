from django.urls import path, include
from apps.videos.views import VideoViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')
urlpatterns = [
        path('', include(router.urls))
]
