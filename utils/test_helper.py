from apps.groups.models import Group, Membership, Invitation
from apps.users.models import User
from apps.videos.models import Video
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import binascii

class TestHelper:
    def __init__(self):
        self.user_count = 0
        self.group_count = 0
        self.video_count = 0

    def create_user(self, is_staff=False, is_superuser=False):
        ''' 
        Creates a new user with a default username, password, and email.
        Username is "user" + the number of users created.
        Password is "password"
        Email is "<username>@test.com"
        
        Args:
            is_staff (bool, optional): Whether the user should be designated as staff. Defaults to False.

        Returns:
            apps.users.models.User: The created User object
        '''
        self.user_count += 1
        username = "user" + str(self.user_count)
        password = "password"
        email = username + "@test.com"
        return User.objects.create(
                username=username,
                password=password, 
                email=email,
                is_staff=is_staff,
                is_superuser=is_superuser
        )

    def create_group(self):
        '''
        Creates a new group with a default name
        Group name is "Group " + the number of groups created.

        Returns:
            apps.groups.models.Group: The created Group object
        '''
        self.group_count += 1
        group_name = "Group " + str(self.group_count)
        return Group.objects.create(group_name=group_name)

    def create_group_by_user(self, user):
        '''
        Creates a new group with a default name and a membership object that
        associates the user as the group's owner.
        Group name is "Group " + the number of groups created.

        Args:
            user (apps.users.models.User): The User object representing the user that creates the group.

        Returns:
            apps.groups.models.Group: The created Group object
        '''
        self.group_count += 1
        group_name = "Group " + str(self.group_count)
        group = Group.objects.create(group_name=group_name)
        self.join_group(group, user, 2)
        return group

    def join_group(self, group, user, role=1):
        '''
        Creates a membership object representing a user joining a group.
        
        Args:
            group (apps.groups.models.Group): The Group object representing the group to join.
            user (apps.users.models.User): The User object representing the user to add to the group.
            role (int, optional): The user's role in the group, represented as an integer. Defaults to 1.

        Returns:
            apps.groups.models.Membership: The Membership object
        '''
        return Membership.objects.create(
                group=group,
                user=user,
                role=role
        )

    def invite_to_group(self, user, group):
        '''
        Creates an invitation to a user to a group.

        Args:
            user (apps.users.models.User): The User object representing the user to invite.
            group (apps.groups.models.Group): The Group object representing the group to invite the user to.

        Returns:
            apps.groups.models.Invitation: The Invitation object
        '''
        return Invitation.objects.create(
                user=user,
                group=group
        )

    def create_file(self, size, name='test', ext='mp4', sig=None):
        '''
        Creates a file with optional signature at the start of the file and fills the remainder with null bytes.

        Args:
            size (int): The size of the file in bytes, including the optional signature.
            name (str, optional): The name of the file. Defaults to 'test'.
            ext (str, optional): The file extension of the file. Defaults to 'mp4'.
            sig (bytes, optional): The signature bytes to be written at the start of the file. Defaults to None.
                NOTE: including sig will make the file have AT LEAST len(sig) bytes, even if size < len(sig).

        Returns:
            django.core.files.uploadedfile.SimpleUploadedFile: The created file as a Django SimpleUploadedFile object.
        '''
        buf = io.BytesIO()
        if sig:
            buf.write(sig)
            size = max(0, size - len(sig))
        # Fill remainder of file with 0's
        buf.write(b'\x00' * size)
        return SimpleUploadedFile(f'{name}.{mp4}', buf.getvalue())

    def create_mp4_file(self, size, name='test'): 
        '''
        Creates a video (mp4) file. Adds an mp4 signature to the start of the file to pass libmagic's mp4 check.

        Args:
            size (int): The size of the video file in bytes. It will be offset by +12 as the signature is 12 bytes.
            name (str, optional): The name of the video file. Defaults to 'test'.

        Returns:
            django.core.files.uploadedfile.SimpleUploadedFile: The created video file as a Django SimpleUploadedFile object.
        '''
        # Hard-coded mp4 signature (specifically ftypmmp4)
        signature = binascii.unhexlify('0000001C667479706D6D7034')
        return self.create_file(size, sig=signature)

    def upload_video(self, creator=None, video_file=None, is_public=True):
        '''
        Creates a video object.

        Args:
            creator (apps.groups.models.User, optional): The username of the creator who uploaded the video. Defaults to None.
            video_file (django.core.files.uploadedfile.SimpleUploadedFile, optional): The video file. Defaults to None.
            is_public (bool, optional): Whether the video should be visible to the public. Defaults to True.

        Returns:
            apps.videos.models.Video: The Video object
        '''
        self.video_count += 1
        video_name = "Video " + str(self.video_count)

        if video_file is None:
            video_file = self.create_mp4_file(1024)

        video = Video.objects.create(
                video_name=video_name, 
                creator=creator,
                video=video_file,
                is_public=is_public
        )
        return video

