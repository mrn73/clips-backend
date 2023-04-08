from rest_framework import serializers
from apps.groups.models import Group, Membership, Invitation
from apps.users.models import User
from apps.users.serializers import UserSerializer

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ['id', 'user', 'group', 'role']
        read_only_fields = ['user', 'group', 'role']

# Serializer for listing members within a group.
class GroupMembersListSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Membership
        fields = ['user', 'role']

class GroupSerializer(serializers.ModelSerializer):
    members = GroupMembersListSerializer(source='membership_set', read_only=True, many=True)

    class Meta:
        model = Group
        fields = ['id', 'group_name', 'members']

class InvitationSerializer(serializers.ModelSerializer):
    username = serializers.ModelField(
            model_field=User._meta.get_field('username'),
            write_only=True
    )

    class Meta:
        fields = ['username']
        model = Invitation

    def __init__(self, instance=None, data=serializers.empty, **kwargs):
        context = kwargs.get('context', None)
        if context:
            group = context.get('group', None)
            sender = context.get('sender', None)
        if context is None or group is None or sender is None:
            raise ValueError("The InvitationSerializer must include a 'context' dict containing 'group' and 'sender'")
        super().__init__(instance=instance, data=data, **kwargs)

    def validate(self, data):
        '''
        Ensures that the user isn't a member of the group and if not, is not
        already invited."
        '''
        group = self.context['group']
        user = self.invited_user
        if Membership.objects.filter(user=user, group=group).exists():
            raise serializers.ValidationError("User is already a member of this group")
        if Invitation.objects.filter(user=user, group=group).exists():
            raise serializers.ValidationError("User is already invited to this group")
        return data

    def validate_username(self, value):
        '''
        Ensure that the invited user exists and is the not the user sending
        the request.
        '''
        invited_user = None
        try:
            invited_user = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Not a valid username")
        if invited_user == self.context['sender']:
            raise serializers.ValidationError("Cannot invite yourself")
        self.invited_user = invited_user
        return value

    def create(self, validated_data):
        user = self.invited_user
        group = self.context['group']
        return Invitation.objects.create(user=user, group_id=group)
