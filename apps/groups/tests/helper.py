from apps.groups.models import Group, Membership, Invitation
from apps.users.models import User

class TestHelper:
    def __init__(self):
        self.user_count = 0
        self.group_count = 0

    def create_user(self):
        ''' 
        Creates a new user with a default username, password, and email.
        Username is "user" + the number of users created.
        Password is "password"
        Email is "<username>@test.com"
        
        Returns:
            User: The created User object
        '''
        self.user_count += 1
        username = "user" + str(self.user_count)
        password = "password"
        email = username + "@test.com"
        return User.objects.create(
                username=username,
                password=password, 
                email=email
        )

    def create_group(self):
        '''
        Creates a new group with a default name
        Group name is "Group " + the number of groups created.

        Returns:
            Group: The created Group object
        '''
        self.group_count += 1
        group_name = "Group " + str(self.group_count)
        return Group.objects.create(group_name=group_name)

    def create_group_by_user(self, user):
        '''
        Creates a new group with a default name and a membership object that
        associates the user as the group's owner.
        Group name is "Group " + the number of groups created.

        Returns:
            Group: The created Group object
        '''
        self.group_count += 1
        group_name = "Group " + str(self.group_count)
        group = Group.objects.create(group_name=group_name)
        self.join_group(group, user, 2)
        return group

    def join_group(self, group, user, role=1):
        '''
        Creates a membership object representing a user joining a group.

        Returns:
            Membership: The Membership object
        '''
        return Membership.objects.create(
                group_id=group,
                user_id=user,
                role=role
        )

    def invite_to_group(self, user, group):
        '''
        Creates an invitation to a user to a group

        Returns:
            Invitation: The Invitation object
        '''
        return Invitation.objects.create(
                user_id=user,
                group_id=group
        )

