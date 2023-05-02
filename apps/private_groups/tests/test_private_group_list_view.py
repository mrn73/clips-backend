from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from utils.test_helper import TestHelper
from apps.private_groups.models import PrivateGroup, PrivateGroupMembership

'''
This module provides tests for creating and listing friendshps.

Classes:
    - GetAllPrivateGroupsTest: Provides methods to test GET on user-private-groups endpoint.
    - CreatePrivateGroupTest: Provides methods to test POST on user-private-groups endpoint.
'''
class GetAllPrivateGroupsTest(APITestCase):
    ''' Tests GET all private groups for a given user ''' 
    def setUp(self):
        helper = TestHelper()

        self.user = helper.create_user()
        self.nonrequested_user = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.group1 = helper.create_priv_group(self.user)
        self.group2 = helper.create_priv_group(self.user)
        self.group3 = helper.create_priv_group(self.user)
        self.url = 'user-private-groups'

    def test_get_all_private_groups_as_request_user(self):
        ''' Should allow a user to see their own private groups '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 3)

    def test_get_all_private_groups_as_nonrequested_user(self):
        ''' Should not permit a user to see private groups that aren't theirs '''
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.nonrequested_user)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_private_groups_as_admin(self):
        ''' Should allow admins to see anyone's privat groups '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 3)

    def test_get_all_private_groups_of_nonexistent_user(self):
        ''' Can't see private groups of a user that doesn't exist '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse(self.url, args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class CreatePrivateGroupTest(APITestCase):
    ''' Tests POST a private group under a given user ''' 
    def setUp(self):
        helper = TestHelper()

        self.user = helper.create_user()
        self.member = helper.create_user()
        self.admin = helper.create_user(is_staff=True)

        self.valid_payload = {
                "group_name": "TEST",
                "members": [
                    reverse('user-detail', args=[self.member.id])
                ]
        }

        self.missing_name_payload = {
                "members": [
                    reverse('user-detail', args=[self.member.id])
                ]
        }

        self.missing_members_payload = {
                "group_name": "TEST",
        }

        self.empty_members_payload = {
                "group_name": "TEST",
                "members": []
        }

        self.members_contains_self_payload = {
                "group_name": "TEST",
                "members": [
                    reverse('user-detail', args=[self.user.id])
                ]
        }

        self.duplicate_members_payload = {
                "group_name": "TEST",
                "members": [
                    reverse('user-detail', args=[self.member.id]),
                    reverse('user-detail', args=[self.member.id]),
                ]
        }


        self.url = 'user-private-groups'

    def test_create_private_group_as_requested_user(self):
        ''' 
        Should be able to create a private group if the user in the request
        is the user in the URL
        '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Ensure the membership objects were made upon group creation
        self.assertEqual(
            len(PrivateGroupMembership.objects.all()),
            len(self.valid_payload['members'])
        )
        
    def test_create_private_group_as_nonrequested_user(self):
        ''' Should not have permission to create a private group under someone else '''
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_private_group_as_admin(self):
        ''' 
        Should not have permission to create a private group under someone
        else.
        '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_private_group_missing_name_field(self):
        ''' Should be a validation error '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.missing_name_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_private_group_missing_members_field(self):
        ''' Should be a validation error '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.missing_members_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_private_group_empty_members_list(self):
        ''' Should be a validation error: must include at least 1 person '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.empty_members_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_private_group_self_as_member(self):
        ''' Should be a validation error: user can't be a member '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.members_contains_self_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_private_group_duplicate_members(self):
        ''' Should be a validation error '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.duplicate_members_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_private_group_under_nonexistent_user(self):
        ''' Should not be allowed -- could be 404 or 403 '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[999]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
