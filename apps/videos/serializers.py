from rest_framework import serializers
from apps.videos.models import Video
from apps.users.models import User
from django.core.files.storage import FileSystemStorage
from utils.defaults import CurrentUserIDDefault
from datetime import datetime, timedelta
from django.utils import timezone
import magic

MAX_FILE_SIZE = 1073741824 #1GB
ALLOWED_TYPES = ['video/mp4'] #mp4 MIME

class VideoSerializer(serializers.ModelSerializer):
    # For deserialization only -- not readable/writable by end user
    creator_id = serializers.HiddenField(default=CurrentUserIDDefault())
    # For serialization only -- readable username
    creator = serializers.StringRelatedField()

    class Meta:
        model = Video
        fields = ['id', 'creator', 'creator_id', 'video_name', 'description', 'is_public', 'video', 'uploaded_at']
        read_only_fields = ['id', 'creator', 'uploaded_at']
        extra_kwargs = {
                'video': {'write_only': True}
        }

    def validate_video(self, value):
        ''' 
        Validates that the video file is within the size limit and of the right content type.
        
        Video file required on initial upload, but not allowed to be changed through PUT/PATCH.
        '''

        if self.instance is None:
            # If this is a new upload, validate size and type.
            if value.size > MAX_FILE_SIZE:
                raise serializers.ValidationError(f"Video size must be less than {MAX_FILE_SIZE / (1024**3)} GB")
            # Check first kb of data (should be safe -- signature usually within first 12 bytes)
            if magic.from_buffer(value.read(1024), mime=True) not in ALLOWED_TYPES:
                raise serializers.ValidationError(f"Video must be of type {', '.join(ALLOWED_TYPES)}")
        else:
            # If this is not a new upload, we can't change the video.
            if value is not None:
                raise serializers.ValidationError("The video file cannot be changed after upload.")
        return value
