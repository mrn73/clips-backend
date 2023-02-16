from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from apps.groups.models import Group, User, Membership
from apps.groups.serializers import GroupSerializer, MembershipSerializer
from django.shortcuts import get_object_or_404

class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    '''
    def get_object(self):
        group = get_object_or_404(self.queryset, pk=self.kwargs.get('pk'))
        group.members = Membership.objects.filter(group_id=group)
        return group
    '''
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.filter(id=self.kwargs['pk'])
        return queryset.prefetch_related('membership_set__user_id')

class GroupJoinView(CreateAPIView):
    serializer_class = MembershipSerializer

    '''
    def perform_create(self, serializer):
        user = self.request.user
        
        try:
            group = Group.objects.get(id=self.kwargs['group_id'])
        except Group.DoesNotExist:
            return Response({"error": "Group does not exist."}, status=status.HTTP_404_NOT_FOUND)
        if not Membership.objects.filter(user_id=user, group_id=group).exists():
            serializer.save(user_id=user, group_id=group)
        else:
            return Response({"error": "This user is a member of this group"}, status=status.HTTP_404_NOT_FOUND)
    '''

class GroupLeaveView(DestroyAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_object(self):
        # Get the group ID in the URL
        group = self.kwargs.get('group_id')
        # Get the current user
        # TODO: change to current user when auth is done
        user = User.objects.get(id=1)
        # Get the membership with the current user and group
        membership = get_object_or_404(self.queryset, group_id=group, user_id=user)
        return membership

