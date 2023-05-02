from django.db import models
from apps.users.models import User

class PrivateGroup(models.Model):
    '''
    Private Groups are groups that only the creator can see.
    Designed to group up friends/users to make it easier for the
    creator to share posts with specific users.
    '''
    group_name = models.CharField(max_length=24)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

class PrivateGroupMembership(models.Model):
    '''
    A mapping between a single Private Group and User.
    '''
    group = models.ForeignKey(PrivateGroup, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_memberships')

    class Meta:
        unique_together = ['group', 'user']
