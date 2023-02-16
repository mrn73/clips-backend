from django.db import models
from apps.users.models import User
from apps.videos.models import Video

# Groups that Users can join. These groups can be used to determine
# video permissions.
class Group(models.Model):
    group_name = models.CharField(max_length=255)

    def __str__(self):
        return self.group_name

# A mapping between a single User and a single Group.
# When a user creates a group, they will automatically be a member with
# the role of 'OWNER'.
class Membership(models.Model):
    class Role(models.IntegerChoices):
        MEMBER = 1
        OWNER = 2

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
    role = models.IntegerField(choices=Role.choices, default=Role.MEMBER)

    class Meta:
        unique_together = ['user_id', 'group_id']

# A mapping of a single group to a single video.
# This allows video restrictions to be set, such as members of "GROUP Y"
# being allowed to view a private video.
class VideoGroup(models.Model):
    video_id = models.ForeignKey(Video, on_delete=models.CASCADE)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
