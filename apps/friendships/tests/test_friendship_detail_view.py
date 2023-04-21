from rest_framework import status
from rest_framework.test import APITestCase
from apps.friendships.models import Friendship
from apps.users.models import User
from django.urls import reverse
from utils.test_helper import TestHelper

'''
This module provides tests for retreiving, updating, or deleting friendship instances.

Classes:
    - RetrieveFriendshipTest: Provides methods to test GET on friendship-detail endpoint.
    - UpdateFriendshipTest: Provides methods to test PATCH on friendship-detail endpoint.
    - DeleteFriendshipTest: Provides methods to test DELETE on friendship-detail endpoint.
'''

class GetSingleFriendshipTest(APITestCase):
    ''' Tests GET a friendship '''
    def setUp(self):
       helper = TestHelper() 

       self.sender = helper.create_user()
       self.receiver = helper.create_user()
       self.nonfriend = helper.create_user()
       self.admin = helper.create_user(is_staff=True)
       self.friendship = helper.make_friends(self.sender, self.receiver)
       self.url = 'friendship-detail'

    def test_get_friendship_as_sender(self):
        ''' Should be able to see the friendship details '''
        self.client.force_authenticate(user=self.sender)
        response = self.client.get(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_friendship_as_receiver(self):
        ''' Should be able to see the friendship details '''
        self.client.force_authenticate(user=self.receiver)
        response = self.client.get(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_friendship_as_nonfriend(self):
        ''' Should not be able to see the friendship '''
        response = self.client.get(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.nonfriend)
        response = self.client.get(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_friendship_as_admin(self):
        ''' Admins can see any friendship '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_friendship_nonexistent(self):
        ''' Can't retrieve a non-existent friendship '''
        self.client.force_authenticate(user=self.sender)
        response = self.client.get(reverse(self.url, args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class UpdateFriendshipTest(APITestCase):
    ''' Tests PATCH a friendship '''

    def setUp(self):
        helper = TestHelper()

        self.sender = helper.create_user()
        self.receiver = helper.create_user()
        self.pending_receiver = helper.create_user()
        self.nonfriend = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.pending_friendship = helper.send_friend_request(self.sender, self.pending_receiver)
        self.friendship = helper.make_friends(self.sender, self.receiver)

        self.accept_friendship_payload = {
                "status": Friendship.Status.ACCEPTED
        }
        self.revert_friendship_payload = {
                "status": Friendship.Status.PENDING
        }
        self.change_sender_payload = {
                "user1": self.nonfriend
        }
        self.change_receiver_payload = {
                "user2": self.nonfriend
        }

        self.url = 'friendship-detail'

    def test_update_pending_friendship_as_non_receiver(self):
        ''' Non receivers should not be able to update the friendship status '''
        # Anonymous user trying to accept the friendship
        response = self.client.patch(
                reverse(self.url, args=[self.pending_friendship.id]),
                self.accept_friendship_payload
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # The sender trying to accept the friendship
        self.client.force_authenticate(user=self.sender)
        response = self.client.patch(
                reverse(self.url, args=[self.pending_friendship.id]),
                self.accept_friendship_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_pending_friendship_as_receiver(self):
        ''' The receiver should be able to change the status to accepted '''
        self.client.force_authenticate(user=self.pending_receiver)
        response = self.client.patch(
                reverse(self.url, args=[self.pending_friendship.id]),
                self.accept_friendship_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_friendship.refresh_from_db()
        self.assertEqual(
                self.pending_friendship.status, 
                self.accept_friendship_payload['status']
        )

    def test_update_pending_friendship_as_admin(self):
        ''' Admins have access to all friendships '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
                reverse(self.url, args=[self.pending_friendship.id]),
                self.accept_friendship_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_friendship.refresh_from_db()
        self.assertEqual(
                self.pending_friendship.status, 
                self.accept_friendship_payload['status']
        )

    def test_update_accepted_friendship_as_receiver(self):
        ''' Should not be able to update an accepted friendship '''
        self.client.force_authenticate(user=self.receiver)
        response = self.client.patch(
                reverse(self.url, args=[self.friendship.id]),
                self.revert_friendship_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_friendship_user_fields(self):
        ''' Should not be able to change the users attached to the friendship '''
        self.client.force_authenticate(user=self.receiver)

        # Change user1 in the friendship
        response = self.client.patch(
                reverse(self.url, args=[self.friendship.id]),
                self.change_sender_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Change user2 in the friendship
        response = self.client.patch(
                reverse(self.url, args=[self.friendship.id]),
                self.change_receiver_payload
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_update_friendship_nonexistent(self):
        ''' Can't update a nonexistent friendship '''
        self.client.force_authenticate(user=self.receiver)
        response = self.client.patch(reverse(self.url, args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_disabled(self):
        ''' Should not be able to PUT (since only status can be changed) '''
        self.client.force_authenticate(user=self.pending_receiver)
        response = self.client.put(
                reverse(self.url, args=[self.pending_friendship.id]),
                self.accept_friendship_payload
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class DeleteFriendshipTest(APITestCase):
    ''' Tests DELETE a friendship '''

    def setUp(self):
        helper = TestHelper()

        self.sender = helper.create_user()
        self.receiver = helper.create_user()
        self.pending_receiver = helper.create_user()
        self.nonfriend = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.pending_friendship = helper.send_friend_request(self.sender, self.pending_receiver)
        self.friendship = helper.make_friends(self.sender, self.receiver)
        self.url = 'friendship-detail'

    def test_delete_friendship_as_sender(self):
        ''' 
        The sender should be able to delete the friendship at any time.
        Delete pending --> canceled; Delete accepted --> removed
        '''
        # Accepted friendship
        self.client.force_authenticate(user=self.sender)
        response = self.client.delete(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Pending friendship
        response = self.client.delete(reverse(self.url, args=[self.pending_friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_friendship_as_receiver(self):
        '''
        The receiver should be able to delete the friendship at any time.
        Delete pending --> declined; Delete accepted --> removed
        '''
        # Accepted friendship
        self.client.force_authenticate(user=self.receiver)
        response = self.client.delete(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Pending friendship
        self.client.force_authenticate(user=self.pending_receiver)
        response = self.client.delete(reverse(self.url, args=[self.pending_friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_friendship_as_admin(self):
        ''' Admins have access to all friendships '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_friendship_as_nonfriend(self):
        ''' Outsiders of this friendship cannot delete the friendship '''
        # Anonymous user
        response = self.client.delete(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # User not involved in friendship
        self.client.force_authenticate(user=self.nonfriend)
        response = self.client.delete(reverse(self.url, args=[self.friendship.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_friendship_nonexistent(self):
        ''' Can't delete a nonexistent friendship '''
        self.client.force_authenticate(user=self.sender)
        response = self.client.delete(reverse(self.url, args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
