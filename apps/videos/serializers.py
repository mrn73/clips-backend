from rest_framework import serializers
from apps.videos.models import Video, Shared
from apps.users.models import User
from apps.users.serializers import UserSerializer
from django.core.files.storage import FileSystemStorage
from utils.defaults import CurrentUserIDDefault
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
import magic

MAX_FILE_SIZE = 1073741824 #1GB
ALLOWED_TYPES = ['video/mp4'] #mp4 MIME

class VideoReadSerializer(serializers.HyperlinkedModelSerializer):
    self = serializers.HyperlinkedIdentityField(
            view_name='video-detail'
    )
    creator = serializers.SerializerMethodField()
    shared_with = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['self', 'id', 'creator', 'video_name', 'description', 'is_public', 'uploaded_at', 'shared_with']
        read_only_fields = ['id', 'creator', 'video_name', 'description', 'is_publc', 'uploaded_at', 'shared_with']

    def get_creator(self, obj):
        return UserSerializer(
                obj.creator, 
                context={'request': self.context['request']}
        ).data

    def get_shared_with(self, obj):
        '''
        Get the users that the video is shared with.

        Takes an optional 'is_list' key in the context dictionary. When set to
        True, the members won't be listed. This makes the response cleaner when
        listing multiple videos, as including shared_with can obfuscate the 
        output.
        '''
        # Set value to None to be later remove in the representation.
        if self.context.get('is_list', False) is True or obj.is_public is True:
            return None

        shared_with = User.objects.filter(shared_videos__video=obj)
        return UserSerializer(
                shared_with,
                many=True,
                context={'request': self.context['request']}
        ).data

    def to_representation(self, instance):
        '''
        Override to_representation to not include 'members' if the value is
        None (triggered from get_members function).
        '''
        rep = super().to_representation(instance)
        if rep['shared_with'] is None:
            del rep['shared_with']
        return rep

class VideoWriteSerializer(serializers.HyperlinkedModelSerializer):
    self = serializers.HyperlinkedIdentityField(
            view_name='video-detail'
    )
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    shared_with = serializers.ListField(
            child=serializers.HyperlinkedRelatedField(
                view_name='user-detail',
                queryset=User.objects.all()
            ),
            allow_empty=True,
            write_only=True,
            required=False
    )

    class Meta:
        model = Video
        fields = ['self', 'id', 'creator', 'creator_id', 'video_name', 'description', 'is_public', 'video', 'uploaded_at', 'shared_with']
        read_only_fields = ['id', 'uploaded_at']
        extra_kwargs = {
                'video': {'write_only': True}
        }

    def create(self, validated_data):
        '''
        Override create method to separately created "shared" instances under
        this video.
        NOTE: if a video is public, the shared users are discarded, since
        being public implicity is available to anyone.
        '''
        shared_with = validated_data.pop('shared_with', None)
        video = super().create(validated_data)
        if video.is_public is False and shared_with is not None:
            self.add_shared_users(video, shared_with)
        return video

    def update(self, instance, validated_data):
        ''' 
        Override update method to account for users to be deleted or added
        to the shared list of a video.
        NOTE: if is_public is true, the shared users will be discarded. Either
        the video needs to already be private, or this request must set the
        is_public field to false along with adding users to the shared list.
        '''
        shared_with = validated_data.pop('shared_with', None)
        if instance.is_public is False and shared_with is not None:
            # Determine which members to add and remove
            old_shared = set(
                    User.objects.filter(shared_videos__video=instance)
            )
            new_shared = set(shared_with)
            to_add = new_shared - old_shared
            to_remove = old_shared - new_shared
            
            # Add any members that are new in the updated members list
            self.add_shared_users(instance, to_add)
            # Delete any members missing in the updated members list
            self.remove_shared_users(instance, to_remove)

        return super().update(instance, validated_data)
     
    def validate_shared_with(self, value):
        '''
        Validates the 'shared_with' field by ensuring there are no duplicate 
        users and that the user is not sharing the video with themself.
        '''
        shared_set = set(value)
        # If the set isn't the same size as the list, there must be duplicates
        if len(value) != len(shared_set):
            raise serializers.ValidationError("Cannot contain duplicate users.")
        #TODO: potential bug -- admin functionality could be broken here. If
        #      an admin tries to change the shared users under another user's
        #      video and wants to add themself, this will not work.
        #      Potential fix: check if the instance is not null. If not, then
        #      check if the instance.creator in shared_set. If instance is null,
        #      then check if the user_id in the kwargs is in the shared_set
        if self.context['request'].user in shared_set:
            raise serializers.ValidationError(
                    "You cannot share a video with yourself"
            )
        return value

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

    def add_shared_users(self, instance, users):
        '''
        Adds users to the shared list of a video.

        Don't need to check for duplication here. Validate_shared_with will fail
        before this is called if there are any duplicates.
        '''
        for user in users:
            Shared.objects.create(
                    user=user,
                    video=instance
            )

    def remove_shared_users(self, instance, users):
        '''
        Removes users from the shared list of a video.
        '''
        for user in users:
            share = Shared.objects.get(video=instance, user=user)
            share.delete()

    def to_representation(self, instance):
        '''
        Override to_representation to use the ReadSerializer so that all
        details of the video are displayed upon successful creation or update. 
        This saves the need to create/update the object and then perform another 
        API call to retrieve the details.
        '''
        rep = VideoReadSerializer(
                instance, 
                context={'request': self.context['request']}
        )
        return rep.to_representation(instance)
