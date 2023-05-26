from django.db import models
from apps.users.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator

class Video(models.Model):
    creator = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    video_name = models.CharField(max_length=100)
    description = models.CharField(max_length=300, null=True)
    video = models.FileField(
            upload_to='uploads/',
            validators=[
                FileExtensionValidator(allowed_extensions=['mp4'])
            ]
    )
    is_public = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(default=timezone.now)

class Shared(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_videos")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="shared_with")
