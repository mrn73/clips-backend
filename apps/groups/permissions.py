from rest_framework.permissions import BasePermission
from apps.groups.models import Membership, Group, Invitation

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        try:
            membership = obj.membership_set.get(user_id=request.user, group_id=obj)
        except Membership.DoesNotExist:
            return False
        return membership.role == 2

class IsMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        return obj.membership_set.filter(user_id=request.user, group_id=obj).exists()

class IsInvited(BasePermission):
    message = "You were not invited to this group."

    def has_permission(self, request, view):
        group_id = view.kwargs.get('group_id')
        user = request.user
        return Invitation.objects.filter(user_id=user, group_id=group_id).exists()

class CanInvite(BasePermission):
    def has_permission(self, request, view):
        group_id = view.kwargs.get('group_id', None)
        user = request.user
        try:
            membership = Membership.objects.get(user_id=user, group_id=group_id)
        except Membership.DoesNotExist:
            return False
        return membership.role == 2
