from django.db import models
from apps.users.models import User
from apps.friendships.managers import FriendshipManager

class Friendship(models.Model):
    '''
    Represents a friendship between two users.

    Two users can be seen as friends if the status of their friendship is ACCEPTED.
    '''
    class Status(models.TextChoices):
        ''' Possible status values for a friendship '''
        PENDING = 'pending'
        ACCEPTED = 'accepted'

    user1 = models.ForeignKey(User, related_name='user1_friends', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='user2_friends', on_delete=models.CASCADE)
    status = models.CharField(choices=Status.choices, default=Status.PENDING, max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FriendshipManager()

    class Meta:
        unique_together = ['user1', 'user2']

    def get_friend_of_user(self, user):
        '''
        Given a user, retrieves the friend of the user within this friendship.
        
        IMPORTANT NOTES: 
            - 'user' should be a user within this friendship
            - If the users aren't prefetched, this function will result in a database hit.
              Make sure to do select_related('user1', 'user2') on the friendship query before
              calling this function, especially if there are mulitple friendship objects.

        Args:
            user (apps.users.models.User): The user for whom to retrieve the friend.

        Returns:
            friend: (apps.users.models.User or None): The friend of the given user in the friendship.
                                                      None if the user doesn't exist in this friendship.
        '''
        friend = None
        if user == self.user1:
            friend = self.user2
        elif user == self.user2:
            friend = self.user1
        return friend

    def __str__(self):
        return f'{self.user1.username} <-> {self.user2.username}'
