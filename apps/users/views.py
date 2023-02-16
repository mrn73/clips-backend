from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.viewsets import ModelViewSet
from apps.users.models import User
from apps.users.serializers import UserSerializer

# Create your views here.
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
