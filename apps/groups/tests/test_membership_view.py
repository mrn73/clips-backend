from rest_framework import status
from rest_framework.test import APITestCase
from apps.groups.models import Group, Membership, Invitation
from apps.users.models import User
from apps.groups.serializers import GroupSerializer
from django.urls import reverse
from utils.test_helper import TestHelper
'''
This module provides tests for each available HTTP method on the Membership model.

Classes:
    - JoinGroupTest: Provides methods to test POST on group-join endpoint.
    - LeaveGroupTest: Provides methods to test DELETE on group-leave endpoint.
'''

class JoinGroupTest(APITestCase):
    ''' Tests POST a membership (join a group) '''

    def setUp(self):
        self.helper = TestHelper()

        self.member = self.helper.create_user()
        self.nonmember = self.helper.create_user()
        self.group = self.helper.create_group_by_user(self.member)

    def test_nonmember_join_valid_group_with_invitation(self):
        self.client.force_authenticate(user=self.nonmember)
        self.helper.invite_to_group(self.nonmember, self.group)
        response = self.client.post(
                reverse('group-join', args=[self.group.id])
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_nonmember_join_valid_group_without_invitation(self):
        self.client.force_authenticate(user=self.nonmember)
        response = self.client.post(
                reverse('group-join', args=[self.group.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_member_join_valid_group(self):
        # This technically can't even happen since you can't invite someone already in the group
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
                reverse('group-join', args=[self.group.id])
        )
        # It would be forbidden since the invite can't exist.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_join_invalid_group(self):
        self.client.force_authenticate(user=self.nonmember)
        response = self.client.post(
                reverse('group-join', args=[999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class LeaveGroupTest(APITestCase):
    ''' Tests DELETE a membership (leave a group) '''

    def setUp(self):
        self.helper = TestHelper()

        self.member = self.helper.create_user()
        self.nonmember = self.helper.create_user()
        self.group = self.helper.create_group_by_user(self.member)

    def test_member_leave_group(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.delete(
                reverse('group-leave', args=[self.group.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Membership.objects.filter(user_id=self.member, group_id=self.group).exists())

    def test_nonmember_leave_group(self):
        # Anonymous user
        response = self.client.delete(
                reverse('group-leave', args=[self.group.id])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Logged in, existing member
        self.client.force_authenticate(user=self.nonmember)
        response = self.client.delete(
                reverse('group-leave', args=[self.group.id])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

