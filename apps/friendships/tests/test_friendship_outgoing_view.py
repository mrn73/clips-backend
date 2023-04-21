from rest_framework import status
from rest_framework.test import APITestCase
from apps.friendships.models import Friendship
from apps.friendships.serializers import OutgoingRequestSerializer
from apps.users.models import User
from django.urls import reverse
from utils.test_helper import TestHelper

'''
This module provides tests for listing outgoing friendshps.

Classes:
    - GetAllOutoingFriendshipsTest: Provides methods to test GET on user-friends-outgoing endpoint.
'''
class GetAllOutgoingFriendshipsTest(APITestCase):
    ''' Tests GET all groups '''

    def setUp(self):
        helper = TestHelper()
        
        self.sender = helper.create_user()
        self.receiver1 = helper.create_user()
        self.receiver2 = helper.create_user()
        self.receiver3 = helper.create_user()
        helper.send_friend_request(self.sender, self.receiver1)
        helper.send_friend_request(self.sender, self.receiver2)
        helper.send_friend_request(self.sender, self.receiver3)
        self.admin = helper.create_user(is_staff=True)
        self.url = 'user-friends-outgoing'

    def test_get_all_requests_as_requested_user(self):
        ''' Should be able to see your own outgoing requests '''
        self.client.force_authenticate(user=self.sender)
        response = self.client.get(reverse(self.url, args=[self.sender.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
                len(response.data), 
                len(Friendship.objects.outgoing_requests_for_user(self.sender))
        )

    def test_get_all_requests_as_nonrequested_user(self):
        ''' 
        If the logged-in user is not the user in the URL, they cannot
        see the outgoing requests
        '''
        response = self.client.get(reverse(self.url, args=[self.sender.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.receiver1)
        response = self.client.get(reverse(self.url, args=[self.sender.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_requests_as_admin(self):
        ''' Admins can see everyone's outgoing requests '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse(self.url, args=[self.sender.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
                len(response.data), 
                len(Friendship.objects.outgoing_requests_for_user(self.sender))
        )
    
    def test_get_all_requests_nonexistent_user(self):
        ''' Can't get requests for a user that doesn't exist '''
        self.client.force_authenticate(user=self.sender)
        response = self.client.get(reverse(self.url, args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
