from rest_framework import status
from rest_framework.test import APITestCase
from apps.friendships.models import Friendship
from apps.friendships.serializers import AcceptedFriendshipSerializer
from apps.users.models import User
from django.urls import reverse
from utils.test_helper import TestHelper

'''
This module provides tests for creating and listing friendshps.

Classes:
    - GetAllFriendsTest: Provides methods to test GET on user-friends endpoint.
    - CreateFriendshipTest: Provides methods to test POST on user-friends endpoint.
'''

class GetAllFriendsTest(APITestCase):
    ''' Tests GET all groups '''

    def setUp(self):
        helper = TestHelper()
        
        self.user = helper.create_user()
        self.friend1 = helper.create_user()
        self.friend2 = helper.create_user()
        self.friend3 = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.url = 'user-friends'

    def test_get_all_friends_as_requested_user(self):
        ''' 
        If the user making the request is equal to the user in the URL, 
        they should be able to see their friends.
        '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = AcceptedFriendshipSerializer(
                Friendship.objects.friendships_of_user(self.user),
                many=True
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_all_friends_as_nonrequested_user(self):
        ''' Should fail to see someone else's friends '''
        # Anonymous user
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # User not in the URL
        self.client.force_authenticate(user=self.friend1)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_friends_as_admin(self):
        ''' Admins can see anyones friends '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = AcceptedFriendshipSerializer(
                Friendship.objects.friendships_of_user(self.user),
                many=True
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_all_friends_of_nonexistent_user(self):
        ''' Can't get friends of a nonexistent user '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse(self.url, args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class CreateFriendshipTest(APITestCase):
    ''' Tests CREATE a friendship (friend request) '''

    def setUp(self):
        helper = TestHelper()

        self.user = helper.create_user()
        self.receiver = helper.create_user()
        self.friend = helper.create_user()
        helper.make_friends(self.user, self.friend)

        self.valid_payload = {
                "to": reverse('user-detail', args=[self.receiver.id])
        }

        self.empty_payload = {}

        self.add_self_payload = {
                "to": self.user
        }

        self.add_existing_friend_payload = {
                "to": self.friend
        }
        self.url = 'user-friends'

    def test_add_friend_as_requested_user(self):
        '''
        Should be able to add a friend if the user in the request
        is the user in the URL
        '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_friend_as_nonrequested_user(self):
        ''' Should not have permission to add a friend under someone else's name '''
        self.client.force_authenticate(user=self.friend)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_friend_missing_to_field(self):
        ''' Should not be able to create a friendship with null '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.empty_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_self_as_friend(self):
        ''' Should not be able to add yourself as a friend '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.add_self_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_friend_when_friendship_exists(self):
        ''' Should not be able to create another instance '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.add_existing_friend_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_friend_under_nonexistent_user(self):
        ''' Can't add a friend under a user that doesn't exist '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[999]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
