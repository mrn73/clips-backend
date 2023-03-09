from rest_framework import status
from rest_framework.test import APITestCase
from apps.groups.models import Group, Membership
from apps.users.models import User
from apps.groups.serializers import GroupSerializer
from django.urls import reverse

'''
This module provides tests for each available HTTP method on the Group model.

Classes:
    - GetAllGroupTest: Provides methods to test GET on group-list endpoint.
    - GetSingleGroupTest: Prodives methods to test GET on group-detail endpoint.
    - CreateGroupTest: Provides methods to test POST on group-list endpoint.
    - UpdateGroupTest: Provides methods to test PUT/PATCH on group-detail endpoint.
    - DeleteGroupTest: Provides methods to test DELETE on group-detail endpoint.
'''

class GetAllGroupsTest(APITestCase):
    ''' Tests GET all groups '''

    def setUp(self):
        Group.objects.create(group_name='Group 1')
        Group.objects.create(group_name='Group 2')
        Group.objects.create(group_name='Group 3')
        Group.objects.create(group_name='Group 4')

        self.user = User.objects.create(
                username='testuser',
                password='password',
                email='user@test.com'
        )

        self.admin = User.objects.create(
                username='admin',
                password='password',
                email='admin@test.com',
                is_staff=True
        )

    def test_get_all_groups_unauthorized(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/groups/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_groups_authorized(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/groups/')
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class GetSingleGroupTest(APITestCase):
    ''' Test GET single group '''

    def setUp(self):
        self.group = Group.objects.create(group_name='Group 1')
        self.member = User.objects.create(
                username='user1',
                password='password',
                email='user1@test.com'
        )
        self.nonmember = User.objects.create(
                username='user2',
                password='password',
                email='user2@test.com'
        )
        Membership.objects.create(group_id=self.group, user_id=self.member)

    def test_get_valid_group_as_member(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(reverse('group-detail', args=[self.group.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_valid_group_as_nonmember(self):
        # Anonymous user
        response = self.client.get(reverse('group-detail', args=[self.group.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Authenticated nonmember
        self.client.force_authenticate(user=self.nonmember)
        response = self.client.get(reverse('group-detail', args=[self.group.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_invalid_group(self): 
        response = self.client.get(reverse('group-detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class CreateGroupTest(APITestCase):
    ''' Tests POST a new group '''

    def setUp(self):
        self.valid_payload = {
                'group_name': 'Group 1'
        }

        self.invalid_payload = {}

        self.user = User.objects.create(
                username='user',
                password='password',
                email='user@test.com'
        )

    def test_create_valid_group_as_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse('group-list'), 
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        membership = Membership.objects.get(group_id=response.data['id'], user_id=self.user)
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, 2)

    def test_create_valid_group_as_anonymous(self):
        response = self.client.post(
                reverse('group-list'), 
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_invalid_group(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse('group-list'),
                self.invalid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UpdateGroupTest(APITestCase):
    ''' Tests PUT/PATCH a group '''

    def setUp(self):
        self.group1 = Group.objects.create(
                group_name='Group 1'
        )

        self.user = User.objects.create(
                username='user',
                password='password',
                email='user@test.com'
        )
        
        self.user2 = User.objects.create(
                username='user2',
                password='password',
                email='user2@test.com'
        )

        Membership.objects.create(
                group_id=self.group1, 
                user_id=self.user,
                role=2
        )

        self.valid_payload = {
                'group_name': 'Changed Group 1'
        }

        self.invalid_payload = {}
        self.url = reverse('group-detail', args=[self.group1.id])

    def test_valid_update_valid_group_authorized(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
                self.url,
                data=self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group1.refresh_from_db()
        self.assertEqual(self.group1.group_name, self.valid_payload['group_name'])

    def test_valid_update_valid_group_unauthorized(self):
        # Anonymous user
        response = self.client.put(
                self.url,
                data=self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated, non-owner user
        self.client.force_authenticate(user=self.user2)
        response = self.client.put(
                self.url,
                data=self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_valid_update_invalid_group(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
                reverse('group-detail', args=[999]),
                data=self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_update(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
                self.url,
                data=self.invalid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DeleteGroupTest(APITestCase):
    ''' Tests DELETE an existing group '''

    def setUp(self):
        self.group1 = Group.objects.create(
                group_name='Group 1'
        )

        self.user = User.objects.create(
                username='user',
                password='password',
                email='user@test.com'
        )
        
        self.user2 = User.objects.create(
                username='user2',
                password='password',
                email='user2@test.com'
        )

        Membership.objects.create(
                group_id=self.group1, 
                user_id=self.user,
                role=2
        )

    def test_delete_valid_group_authorized(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
                reverse('group-detail', args=[self.group1.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(id=self.group1.id).exists())

    def test_delete_valid_group_unauthorized(self):
        # Anonymous user
        response = self.client.delete(
                reverse('group-detail', args=[self.group1.id])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated, non-owner user
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(
                reverse('group-detail', args=[self.group1.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_invalid_group(self):
        response = self.client.delete(
                reverse('group-detail', args=[999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
