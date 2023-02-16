from django.urls import path, include
from apps.users.views import UserViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
urlpatterns = [
        path('', include(router.urls))
]
