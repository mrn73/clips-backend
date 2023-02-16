from django.db import models
from apps.users.models import User

class Video(models.Model):
    creator_id = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    video_name = models.CharField(max_length=100)
    description = models.CharField(max_length=300, null=True)
    video = models.FileField(
                upload_to='uploads/',
                null = True)
    is_public = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField()
