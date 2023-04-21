from django.db.models import Manager, Q

class FriendshipManager(Manager):
    def friendships_of_user(self, user):
        '''
        Retrieve friendships of a given user that are in the accepted status.
        
        Uses select_related to prefetch the users of this friendship in case the users' info is needed.

        Args:
            user (apps.users.models.User): The user for whom to retrieve friendships.

        Returns:
            QuerySet: A QuerySet containing the friendships that are accepted and involve the given user.

        Example:
            friendships = Friendship.objects.friendships_of_user(user)
            for f in friendships:
                # Due to select_related, this won't query the database
                print(f.user1.username)
        '''
        return self.filter(Q(user1=user) | Q(user2=user), status='accepted').select_related('user1', 'user2')

    def pending_friendships_of_user(self, user):
        '''
        Retrieve all pending friendships (incoming/outgoing) for a given user.

        Uses select_related to prefetch the users of this friendship in case the users' info is needed.

        Args:
            user (apps.users.models.User): The user for whom to retrieve pending friendship requests.

        Returns:
            QuerySet: A QuerySet containing the friendships that are pending for the given user.

        Example:
            pending = Friendship.objects.pending_friendships_of_user(user)
        '''

        return self.filter(Q(user1=user) | Q(user2=user), status='pending').select_related('user1', 'user2')
    def incoming_requests_for_user(self, user):
        '''
        Retrieve friendships that are incoming and pending for a given user.

        Uses select_related to prefetch the users of this friendship in case the users' info is needed.

        Args:
            user (apps.users.models.User): The user for whom to retrieve incoming friendship requests.

        Returns:
            QuerySet: A QuerySet containing the friendships that are pending and have user1 set to user.

        Example:
            incoming_requests = Friendship.objects.incoming_requests_for_user(user)
        '''
        return self.filter(user2=user, status='pending').select_related('user1', 'user2')

    def outgoing_requests_for_user(self, user):
        '''
        Retrieve friendships that are outgoing and pending for a given user.

        Uses select_related to prefetch the users of this friendship in case the users' info is needed.

        Args:
            user (apps.users.models.User): The user for whom to retrieve incoming friendship requests.

        Returns:
            QuerySet: A QuerySet containing the friendships that are pending and have user2 set to user.

        Example:
            incoming_requests = Friendship.objects.incoming_requests_for_user(user)
        '''
        return self.filter(user1=user, status='pending').select_related('user1', 'user2')

