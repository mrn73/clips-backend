from rest_framework import serializers
from apps.friendships.models import Friendship
from apps.users.models import User
from apps.users.serializers import UserSerializer

class CreateFriendshipSerializer(serializers.HyperlinkedModelSerializer):
    '''
    Serializer class for creating a friendship.
    Made this into its own class due to it being very different from 
    listing/details representation.
    NOTE: should only be used when POSTING!
    '''
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    self = serializers.HyperlinkedIdentityField(
        view_name='friendship-detail',
        lookup_field='id'
    )
    to = serializers.HyperlinkedRelatedField(
        queryset=User.objects.all(),
        view_name='user-detail'
    )
 
    class Meta:
        model = Friendship
        fields = ['self', 'sender', 'to']

    def validate(self, data):
        if data['sender'] == data['to']:
            raise serializers.ValidationError("You cannot add yourself as a friend.")
        if Friendship.objects.filter(user1=data['sender'], user2=data['to']).exists():
            raise serializers.ValidationError("Friendship already exists.")
        return data

    def create(self, validated_data):
        validated_data['user1'] = validated_data.pop('sender')
        validated_data['user2'] = validated_data.pop('to')
        return super().create(validated_data)

class ListFriendshipSerializer(serializers.HyperlinkedModelSerializer):
    self = serializers.HyperlinkedIdentityField(
        view_name='friendship-detail',
        lookup_field='id'
    )
    friend = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ['self', 'friend']

    def get_friend(self, obj):
        user = self.context['request'].user
        friend = None
        if obj.user1 == user:
            friend = UserSerializer(obj.user2, context={'request': self.context['request']}).data
        elif obj.user2 == user:
            friend = UserSerialiazer(obj.user1, context={'request': self.context['request']}).data
        return friend

class FriendshipSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Friendship
        fields = ['self', 'user1', 'user2', 'status']
        read_only_fields = ['user1', 'user2']

    def update(self, instance, validated_data):
        if instance.status != 'accepted':
            super().update(instance,  validated_data)
        return instance
