from rest_framework import serializers
from apps.groups.models import Group, Membership
from apps.users.models import User
from apps.users.serializers import UserSerializer

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ['id', 'user_id', 'group_id', 'role']

# Serializer for listing members within a group.
class GroupMembersListSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user_id.username')

    class Meta:
        model = Membership
        fields = ['user', 'role']

class GroupSerializer(serializers.ModelSerializer):
    members = GroupMembersListSerializer(source='membership_set', read_only=True, many=True)

    class Meta:
        model = Group
        fields = ['id', 'group_name', 'members']
