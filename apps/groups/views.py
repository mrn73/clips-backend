from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status, permissions, exceptions
from apps.groups.models import Group, User, Membership, Invitation
from apps.groups.serializers import GroupSerializer, MembershipSerializer, InvitationSerializer
from apps.groups.permissions import IsOwner, IsMember, IsInvited

# Group CREATE, READ, UPDATE, DELETE view.
class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    # When loading groups, prefetch their related memberships and the users
    # associated with those memberships.
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.prefetch_related('membership_set__user_id')
 
    # All group actions must be by an authenticated user.
    # Deleting or updating a group is done by the owner.
    def get_permissions(self):
        permission_classes = [permissions.IsAdminUser]
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        if self.action == 'retrieve':
            permission_classes = [IsMember | permissions.IsAdminUser]
        if self.action in ['destroy', 'update', 'partial_update']:
            permission_classes = [permissions.IsAdminUser | IsOwner]
        return [permission() for permission in permission_classes]

    # When creating a group, the creator must become a member of the group
    # with their role set as owner.
    def perform_create(self, serializer):
        group = serializer.save()
        user = self.request.user
        Membership.objects.create(user_id=user, group_id=group, role=2)

# Membership CREATE view, where a user joins a group.
class GroupJoinView(CreateAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsInvited]
    
    # Before joining a group, ensures the group exists and that the user
    # is not already a member.
    def perform_create(self, serializer): 
        user = self.request.user
        try:
            group = Group.objects.get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise exceptions.NotFound("Group does not exist")
        if Membership.objects.filter(user_id=user, group_id=group).exists():
            raise exceptions.ValidationError({"detail": "This user is already a member of this group"})
        serializer.save(user_id=user, group_id=group)

# Membership DESTROY view, where a user leaves a group.
class GroupLeaveView(DestroyAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Ensures that the user is a member of the group before leaving.
    def get_object(self):
        # Get the group ID in the URL
        group = self.kwargs.get('group_id')
        # Get the current user
        user = self.request.user
        # Get the membership with the current user and group
        membership = None
        try:
            membership = Membership.objects.get(group_id=group, user_id=user)
        except Membership.DoesNotExist:
            raise exceptions.NotFound("Membership does not exist")
        return membership

    # Removes a member from the group.
    # If the owner leaves, the group is deleted along with all of its memberships.
    def perform_destroy(self, instance):
        if instance.role == 2:
            instance.group_id.delete_with_memberships()
        else:
            instance.delete()

class GroupInviteView(CreateAPIView):
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def perform_create(self, serializer): 
        if self.request.user.username == self.request.data.get('username', None):
            raise exceptions.ValidationError({"detail": "You cannot invite yourself to a group."})
        try:
            group = Group.objects.get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise exceptions.NotFound("Group does not exist")
        try:
            user = User.objects.get(username=self.request.data.get('username', None))
        except User.DoesNotExist:
            raise exceptions.NotFound("User does not exist")
        if Invitation.objects.filter(user_id=user, group_id=group).exists():
            raise exceptions.ValidationError({"detail": "This user is already invited to this group."})
        serializer.save(user_id=user, group_id=group)
