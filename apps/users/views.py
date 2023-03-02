from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.viewsets import ModelViewSet
from apps.users.models import User
from apps.users.serializers import UserSerializer
from apps.users.permissions import IsUserOrReadOnly
from rest_framework import permissions

# Create your views here.
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser | IsUserOrReadOnly]

