from rest_framework import serializers
from apps.users.models import User

class UserSerializer(serializers.ModelSerializer): 
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name']
        extra_kwargs = {
                'password': {'write_only': True},
                'email': {'write_only': True},
                'first_name': {'write_only': True},
                'last_name': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
