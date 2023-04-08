from django.db import models
from apps.users.models import User
from apps.videos.models import Video

class Group(models.Model):
    '''
    Groups that Users can join. These groups can be used to determine
    video permissions.
    '''
    group_name = models.CharField(max_length=255)

    def delete_with_memberships(self):
        self.membership_set.all().delete()
        self.delete()

    def __str__(self):
        return self.group_name

class Membership(models.Model):
    '''
    A mapping between a single User and a single Group.
    When a user creates a group, they will automatically be a member with
    the role of 'OWNER'.
    '''
    class Role(models.IntegerChoices):
        MEMBER = 1
        OWNER = 2

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    role = models.IntegerField(choices=Role.choices, default=Role.MEMBER)

    class Meta:
        unique_together = ['user', 'group']

    def get_owner(self, group):
        '''
        Gets  membership object that corresponds to the owner of the group.
        
        Args:
            group (int/Group) : The group's primary key or group object
        Returns:
            Membership/None :  Membership object or None if none exists 
        '''
        try:
            return Membership.objects.filter(group=group).get(role=2)
        except Membership.DoesNotExist:
            return None
        except Membership.MultipleObjectsReturned:
            return None

    def __str__(self):
        return "member: " + self.user

class Invitation(models.Model):
    '''
    An invitation to the group.
    Once an invite is accepted, it will be deleted from this table.
    '''
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'group']

class VideoGroup(models.Model):
    '''
    A mapping of a single group to a single video.
    This allows video restrictions to be set, such as members of "GROUP Y"
    being allowed to view a private video.
    '''
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
