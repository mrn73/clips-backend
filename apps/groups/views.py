from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status, permissions, exceptions
from apps.groups.models import Group, User, Membership, Invitation
from apps.groups.serializers import GroupSerializer, MembershipSerializer, InvitationSerializer
from apps.groups.permissions import IsOwner, IsMember, IsInvited, CanInvite

class GroupViewSet(ModelViewSet):
    ''' Group CREATE, READ, UPDATE, DELETE view. '''

    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    # When loading groups, prefetch their related memberships and the users
    # associated with those memberships.
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.prefetch_related('membership_set__user')
 
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
        Membership.objects.create(user=user, group=group, role=2)

class GroupJoinView(CreateAPIView):
    ''' Membership CREATE view, where a user joins a group. '''

    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            group = Group.objects.get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise exceptions.NotFound("Group does not exist")

        user = self.request.user 
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not Invitation.objects.filter(user_id=user, group_id=group).exists():
            raise exceptions.PermissionDenied("You were not invited to this group.")

        serializer.save(user=user, group=group) 
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class GroupLeaveView(DestroyAPIView):
    ''' Membership DESTROY view, where a user leaves a group. '''

    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Ensures that the user is a member of the group before leaving.
    def get_object(self):
        # Get the group ID in the URL
        group_id = self.kwargs.get('group_id')
        # Get the current user
        user = self.request.user
        # Get the membership with the current user and group
        membership = None
        try:
            membership = Membership.objects.get(group=group_id, user=user)
        except Membership.DoesNotExist:
            raise exceptions.NotFound("Membership does not exist")
        return membership

    # Removes a member from the group.
    # If the owner leaves, the group is deleted along with all of its memberships.
    def perform_destroy(self, instance):
        if instance.role == 2:
            instance.group.delete_with_memberships()
        else:
            instance.delete()

class GroupInviteView(CreateAPIView):
    ''' Invitation CREATE view, where a user is invited to a group. '''

    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated, CanInvite]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['group'] = self.kwargs['group_id']
        context['sender'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        # Preliminary check to ensure the group exists
        try:
            group = Group.objects.get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            raise exceptions.NotFound("Group does not exist")
        # Proceed with creation as normal
        return super().create(request, *args, **kwargs) 
