from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from utils.test_helper import TestHelper

'''
This module provides tests for retrieving, updating, or deleting private group instances.

Classes:
    - GetSinglePrivateGroupsTest: Provides methods to test GET on private-group-detail endpoint.
    - UpdatePrivateGroupTest: Provides methods to test POST on private-group-detail endpoint.
    - DeletePrivateGroupTest: Provides methods to test POST on private-group-detail endpoint.
'''

class GetSinglePrivateGroupTest(APITestCase):
    ''' Tests GET an instance of Private Group '''
    def setUp(self):
        helper = TestHelper()

        self.creator = helper.create_user()
        self.members = [helper.create_user() for i in range(3)]
        self.noncreator = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.priv_group = helper.create_priv_group(
                self.creator,
                self.members
        )
        self.url = 'private-group-detail'

    def test_get_private_group_as_creator(self):
        ''' Should be able to see the group details '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.get(reverse(self.url, args=[self.priv_group.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_private_group_as_noncreator(self):
        ''' Should not be able to see the private group '''
        # Anonymous user
        response = self.client.get(reverse(self.url, args=[self.priv_group.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Noncreator user
        self.client.force_authenticate(user=self.noncreator)
        response = self.client.get(reverse(self.url, args=[self.priv_group.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_private_group_as_admin(self):
        ''' Should be able to see any private group '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse(self.url, args=[self.priv_group.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_private_group_nonexistent(self):
        ''' Can't get a privat group that doesn't exist '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse(self.url, args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class UpdatePrivateGroupTest(APITestCase):
    ''' Tests PUT/PATCH an instance of Private Group '''
    def setUp(self):
        helper = TestHelper()

        self.creator = helper.create_user()
        self.noncreator = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.members = [helper.create_user() for i in range(3)]
        self.member_urls = list(map(
                lambda user: reverse('user-detail', args=[user.id]),
                self.members
        ))
        self.priv_group = helper.create_priv_group(
                self.creator,
                self.members
        )

        # Remove 1 member from the group and change the name
        self.update_all_fields_payload = {
                'group_name': 'CHANGED',
                'members': self.member_urls[:-1]
        }

        # Remove 1 member from the group
        self.update_members_field_payload = {
                'members': self.member_urls[:-1]
        }

        # Change the name
        self.update_name_field_payload = {
                'group_name': 'CHANGED'
        }

        self.url = 'private-group-detail'

    def test_put_private_group_as_creator(self):
        ''' Should be able to update one's own private group '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.put(
                reverse(self.url, args=[self.priv_group.id]),
                self.update_all_fields_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.priv_group.refresh_from_db()
        self.assertEqual(
                self.priv_group.group_name,
                self.update_all_fields_payload['group_name']
        )
        self.assertEqual(
                list(map(
                    lambda user_id: reverse('user-detail', args=[user_id]),
                    self.priv_group.memberships.values_list('user', flat=True)
                )),
                self.update_all_fields_payload['members']
        )

    def test_put_private_group_as_noncreator(self):
        ''' Should not have permission to edit someone else's private group '''
        # Anonymous user
        response = self.client.put(
                reverse(self.url, args=[self.priv_group.id]),
                self.update_all_fields_payload
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Noncreator user
        self.client.force_authenticate(user=self.noncreator)
        response = self.client.put(
                reverse(self.url, args=[self.priv_group.id]),
                self.update_all_fields_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_private_group_as_admin(self):
        ''' Should be able to edit anyone's private group '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
                reverse(self.url, args=[self.priv_group.id]),
                self.update_all_fields_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.priv_group.refresh_from_db()
        self.assertEqual(
                self.priv_group.group_name,
                self.update_all_fields_payload['group_name']
        )
        self.assertEqual(
                list(map(
                    lambda user_id: reverse('user-detail', args=[user_id]),
                    self.priv_group.memberships.values_list('user', flat=True)
                )),
                self.update_all_fields_payload['members']
        )

    def test_patch_private_group_name(self):
        ''' Should be able to patch just the name as the creator '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.patch(
                reverse(self.url, args=[self.priv_group.id]),
                self.update_name_field_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.priv_group.refresh_from_db()
        self.assertEqual(
                self.priv_group.group_name,
                self.update_name_field_payload['group_name']
        )

    def test_patch_private_group_members(self):
        ''' Should be able to patch just the members as the creator '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.patch(
                reverse(self.url, args=[self.priv_group.id]),
                self.update_members_field_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.priv_group.refresh_from_db()
        self.assertEqual(
                list(map(
                    lambda user_id: reverse('user-detail', args=[user_id]),
                    self.priv_group.memberships.values_list('user', flat=True)
                )),
                self.update_all_fields_payload['members']
        )

    def test_patch_private_group_as_noncreator(self):
        ''' Should not have permission to patch someone else's group '''
        self.client.force_authenticate(user=self.noncreator)
        response = self.client.patch(
                reverse(self.url, args=[self.priv_group.id]),
                self.update_members_field_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_private_group_nonexistent(self):
        ''' Can't patch a groupp that doesn't exist '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.put(
                reverse(self.url, args=[999]),
                self.update_members_field_payload
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class DeletePrivateGroupTest(APITestCase):
    ''' Tets DELETE a private group '''

    def setUp(self):
        helper = TestHelper()

        self.creator = helper.create_user()
        self.noncreator = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.priv_group = helper.create_priv_group(self.creator)
        
        self.url = 'private-group-detail'

    def test_delete_private_group_as_creator(self):
        ''' Should be able to delete your own private group '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.delete(
                reverse(self.url, args=[self.priv_group.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_private_group_as_noncreator(self):
        ''' Should not have permission to delete a group you don't own '''
        # Anonymous user
        response = self.client.delete(
                reverse(self.url, args=[self.priv_group.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Noncreator user
        self.client.force_authenticate(user=self.noncreator)
        response = self.client.delete(
                reverse(self.url, args=[self.priv_group.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_private_group_as_admin(self):
        ''' Should be allowed to delete anyone's private group '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
                reverse(self.url, args=[self.priv_group.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_private_group_nonexistent(self):
        ''' Can't delete a private group that doesn't exist '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.delete(
                reverse(self.url, args=[999]),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
