from rest_framework import status
from rest_framework.test import APITestCase
from utils.test_helper import TestHelper
from django.urls import reverse

'''
This module provides tests for each available HTTP method on the Invitation model.

Classes:
    - CreateInviteTest: Provides methods to test POST on group-invite endpoint.
'''

class CreateInviteTest(APITestCase):
    ''' Tests POST an invitation (invite to a group) '''

    def setUp(self):
        self.helper = TestHelper()

        self.nonmember = self.helper.create_user()
        self.member = self.helper.create_user()
        self.owner = self.helper.create_user()
        self.group = self.helper.create_group_by_user(self.owner)
        self.helper.join_group(self.group, self.member)

    def test_owner_invite_nonmember(self):
        ''' owner invites nonmember -- OK '''
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
                reverse('group-invite', args=[self.group.id]),
                {'username': self.nonmember.username}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_owner_invite_nonmember_twice(self):
        ''' owner invites a nonmember with an active pending invitation -- not allowed '''
        self.client.force_authenticate(user=self.owner)
        self.client.post(
                reverse('group-invite', args=[self.group.id]),
                {'user': self.nonmember.username}
        )
        response = self.client.post(
                reverse('group-invite', args=[self.group.id]),
                {'user': self.nonmember.username}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_invite_member(self):
        ''' owner invites an existing member -- not allowed '''
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
                reverse('group-invite', args=[self.group.id]),
                {'user': self.member.username}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_invite_self(self):
        ''' owner invites themself -- now allowed '''
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
                reverse('group-invite', args=[self.group.id]),
                {'user': self.nonmember.username}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_invite_nonexistent_user(self):
        ''' owner invites a user that doesn't exist -- not allowed '''
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
                reverse('group-invite', args=[self.group.id]),
                {'user': 'doesnotexist'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonowner_invite_user(self):
        ''' non-owner invites any user -- not allowed '''
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
                reverse('group-invite', args=[self.group.id]),
                {'user': self.nonmember.username}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    
    def test_unauthenticated(self):
        ''' anonymous user tries to access this endpoint -- not allowed '''
        response = self.client.post(
                reverse('group-invite', args=[self.group.id]),
                {'user': self.nonmember.username}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
