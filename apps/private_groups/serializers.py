from rest_framework import serializers
from apps.private_groups.models import PrivateGroup, PrivateGroupMembership
from apps.users.models import User
from apps.users.serializers import UserSerializer

class PrivateGroupReadSerializer(serializers.HyperlinkedModelSerializer):
    '''
    Serializer class for displaying private groups.
    '''
    self = serializers.HyperlinkedIdentityField(
            view_name='private-group-detail'
    )
    members = serializers.SerializerMethodField()

    class Meta:
        model = PrivateGroup
        fields = ['self', 'group_name', 'creator', 'members']
        read_only_fields = ['self', 'group_name', 'creator', 'members']

    def get_members(self, obj):
        '''
        Get the members (users) in the group.

        Takes an optional 'is_list' key in the context dictionary. When set to
        True, the members won't be listed. This makes the response cleaner when
        listing multiple groups, as including members can obfuscate the output.
        '''
        # Set value to None to be later remove in the representation.
        if self.context.get('is_list', False) is True:
            return None
        
        members = User.objects.filter(private_memberships__group=obj)

        return UserSerializer(
                members,
                many=True,
                context={'request': self.context['request']}
        ).data

    def to_representation(self, instance):
        '''
        Override to_representation to not include 'members' if the value is
        None (triggered from get_members function).
        '''
        rep = super().to_representation(instance)
        if rep['members'] is None:
            del rep['members']
        return rep

class PrivateGroupWriteSerializer(serializers.HyperlinkedModelSerializer):
    '''
    Serializer class for creating and editing private groups.

    NOTE: requires the request in a context dictionary.
    '''
    self = serializers.HyperlinkedIdentityField(
            view_name='private-group-detail'
    )
    creator = serializers.HiddenField(
            default=serializers.CurrentUserDefault()
    )
    members = serializers.ListField(
            child=serializers.HyperlinkedRelatedField(
                view_name='user-detail',
                queryset=User.objects.all()
            ),
            allow_empty=False,
            write_only=True
    )

    class Meta:
        model = PrivateGroup
        fields = ['self', 'group_name', 'creator', 'members']

    def create(self, validated_data):
        '''
        Override create method to separately create memberships linked
        to this private group.
        '''
        members = validated_data.pop('members', None)
        private_group = super().create(validated_data)
        self.add_members(private_group, members)
        return private_group

    def update(self, instance, validated_data):
        ''' 
        Override update method to account for memberships to be deleted
        or added.
        '''
        members = validated_data.pop('members', None)
        if members is not None:
            # Determine which members to add and remove
            old_members = set(
                    User.objects.filter(private_memberships__group=instance)
            )
            new_members = set(members)
            to_add = new_members - old_members
            to_remove = old_members - new_members
            
            # Add any members that are new in the updated members list
            self.add_members(instance, to_add)
            # Delete any members missing in the updated members list
            self.remove_members(instance, to_remove)

        return super().update(instance, validated_data)
     
    def validate_members(self, value):
        '''
        Validates the 'members' field by ensuring there are no duplicate users
        and that the user is not adding themself as a member.
        '''
        member_set = set(value)
        # If the set isn't the same size as the list, there must be duplicates
        if len(value) != len(member_set):
            raise serializers.ValidationError("Cannot contain duplicate users.")
        if self.context['request'].user in member_set:
            raise serializers.ValidationError(
                    "You cannot be a member of your own private group."
            )
        return value

    def add_members(self, instance, users):
        '''
        Adds members to a group.

        Don't need to check for duplication here. Validate_members will fail
        before this is called if there are any duplicates.
        '''
        for user in users:
            PrivateGroupMembership.objects.create(
                    group=instance,
                    user=user
            )

    def remove_members(self, instance, users):
        '''
        Removes members from a group.
        '''
        for user in users:
            membership = PrivateGroupMembership.objects.get(group=instance, user=user)
            membership.delete()

    def to_representation(self, instance):
        '''
        Override to_representation to use the ReadSerializer so that all
        details of the private group are displayed upon successful creation
        or update. This saves the need to create/update the object and then
        perform another API call to retrieve the details.
        '''
        rep = PrivateGroupReadSerializer(
                instance, 
                context={'request': self.context['request']}
        )
        return rep.to_representation(instance)
