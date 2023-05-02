from rest_framework import permissions
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from apps.private_groups.serializers import PrivateGroupReadSerializer, PrivateGroupWriteSerializer
from apps.private_groups.models import PrivateGroup, PrivateGroupMembership
from apps.private_groups.permissions import IsRequestedUser, IsCreator
from apps.users.models import User
from django.shortcuts import get_object_or_404

'''
Handles views for PrivateGroups and PrivateGroupMembers.

Naming convention notes:
    'ListView' = collection/
    'DetailView' = collection/<collection_item>/
'''
class PrivateGroupListView(ListCreateAPIView):
    '''
    List and create private groups.

    Should be nested under user-detail view.
    '''
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsRequestedUser | permissions.IsAdminUser]
        else:
            # Admins shouldn't be able to create for another user since the
            # serializer sets the user making the request as the creator.
            permission_classes = [IsRequestedUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        return (PrivateGroupReadSerializer if self.request.method == 'GET'
                else PrivateGroupWriteSerializer)

    def get_serializer_context(self):
        ''' 
        Override this function to add 'is_list' key into the context 
        dictionary. In the serializer, if 'is_list' is true, then we won't
        list the members in the serialized output.
        '''
        context = super().get_serializer_context()
        if self.request.method == 'GET':
            context['is_list'] = True
        return context
    
    def get_queryset(self):
        user = get_object_or_404(User.objects.all(), id=self.kwargs['user_id'])
        return PrivateGroup.objects.filter(creator=user)

class PrivateGroupDetailView(RetrieveUpdateDestroyAPIView):
    ''' View to retrieve, update, or delete a Private Group instance. '''

    queryset = PrivateGroup.objects.all()
    permission_classes = [IsCreator | permissions.IsAdminUser]

    def get_serializer_class(self):
        return (PrivateGroupReadSerializer if self.request.method == 'GET'
                else PrivateGroupWriteSerializer)
