from rest_framework import serializers
from apps.friendships.models import Friendship
from apps.users.models import User
from apps.users.serializers import UserSerializer
from django.db.models import Q
from django.urls import reverse

class CreateFriendshipSerializer(serializers.HyperlinkedModelSerializer):
    '''
    Serializer class for creating new friendships.

    Designed to be used for creating or retrieving a friendship instance.
    
    NOTE: requires "request" in the context dict from the calling view.
    '''
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    to = serializers.HyperlinkedRelatedField(
        queryset=User.objects.all(),
        view_name='user-detail',
        write_only=True
    )
 
    class Meta:
        model = Friendship
        fields = ['self', 'sender', 'to', 'user1', 'user2', 'status']
        read_only_fields = ['user1', 'user2', 'status']

    def validate(self, data):
        sender = data['sender']
        to = data['to']

        if sender == to:
            raise serializers.ValidationError({"to": "You cannot add yourself as a friend."})

        friendship = Friendship.objects.filter(Q(user1=sender, user2=to) | Q(user1=to, user2=sender)).first()
        if friendship:
            raise serializers.ValidationError([
                "Friendship already exists. Modify the friendship at the existing URL.",
                {
                    "friendship": self.context['request'].build_absolute_uri('/')[:-1] + reverse('friendship-detail', args=[friendship.id])
                }
            ])
        return data

    def create(self, validated_data):
        # Map custom serializer fields to the actual fields within the model.
        validated_data['user1'] = validated_data.pop('sender')
        validated_data['user2'] = validated_data.pop('to')
        return super().create(validated_data)

class FriendshipSerializer(serializers.HyperlinkedModelSerializer):
    '''
    Serializer class for displaying friendship details.
    '''
    class Meta:
        model = Friendship
        fields = ['self', 'user1', 'user2', 'status']
        read_only_fields = ['user1', 'user2']

class AcceptedFriendshipSerializer(serializers.HyperlinkedModelSerializer):
    '''
    Serializer class for displaying a list of friends (status = accepted).
    
    NOTE: requires "request" in the context dict from the calling view.
    '''
    friend = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ['self', 'friend']

    def get_friend(self, obj):
        # Displays the friend of a user by choosing the user in the friendship
        # that isn't the user in the url.
        user_id = self.context['view'].kwargs.get('user_id')
        friend = obj.user2 if obj.user1.id == user_id else obj.user1
        return UserSerializer(friend, context={'request': self.context['request']}).data

class IncomingRequestSerializer(serializers.HyperlinkedModelSerializer):
    '''
    Serializer class for displaying incoming friend requests.

    NOTE: requires "request" in the context dict from the calling view.
    '''
    user = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ['self', 'user']

    def get_user(self, obj):
        return UserSerializer(
                obj.user1,
                context={'request': self.context['request']}
        ).data

class OutgoingRequestSerializer(serializers.HyperlinkedModelSerializer):
    #TODO: Can combine this with the above serializer and switch obj.user depending on context
    '''
    Serializer class for displaying outgoing friend requests.

    NOTE: requires "request" in the context dict from the calling view.
    '''
    user = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ['self', 'user']

    def get_user(self, obj):
        return UserSerializer(
                obj.user2,
                context={'request': self.context['request']}
        ).data
