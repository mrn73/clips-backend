from rest_framework import status
from rest_framework.test import APITestCase
from utils.test_helper import TestHelper
from django.urls import reverse
from apps.videos.serializers import VideoReadSerializer, VideoWriteSerializer
from apps.videos.models import Video, Shared
from django.db.models import Q
from django.test import override_settings
from decouple import config
import shutil

'''
This module provides tests retrieving, updating, and deleting a video.

Classes:
    - GetSingleVideoTest: Provides methods to test GET on video-detail endpoint.
    - UpdateVideoTest: Provides methods to test PATCH on video-detail endpoint.
    - DeleteVideoTest: Provides methods to test DELETE on video-detail endpoint.
'''
@override_settings(MEDIA_ROOT=config('VIDEO_STORAGE_TEST'))
class GetSingleVideoTest(APITestCase):
    def setUp(self):
        helper = TestHelper()
        self.creator = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.shared_user = helper.create_user()
        self.unshared_user = helper.create_user()
        self.video = helper.upload_video(
                creator=self.creator,
                is_public=False
        )
        self.public_video = helper.upload_video()
        helper.share_video_with_user(self.video, self.shared_user)

        self.url = 'video-detail'

    def test_get_private_video_as_admin(self):
        ''' Should be able to get any video '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse(self.url, args=[self.video.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_private_video_as_creator(self):
        ''' Should be able to get one's own video '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.get(reverse(self.url, args=[self.video.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_private_video_as_shared_user(self):
        ''' Should be able to get a video that is shared with them '''
        self.client.force_authenticate(user=self.shared_user)
        response = self.client.get(reverse(self.url, args=[self.video.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_private_video_as_unshared_user(self):
        ''' Should not have permission to see the video '''
        self.client.force_authenticate(user=self.unshared_user)
        response = self.client.get(reverse(self.url, args=[self.video.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_public_video_as_any_user(self):
        ''' Any user should be able to see a public video '''
        response = self.client.get(reverse(self.url, args=[self.public_video.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_video_nonexistent(self):
        ''' Can't retrieve a video that doesn't exist '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.get(reverse(self.url, args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def tearDown(self):
        shutil.rmtree(
                config('VIDEO_STORAGE_TEST'),
                ignore_errors=True
        )

@override_settings(MEDIA_ROOT=config('VIDEO_STORAGE_TEST'))
class UpdateVideoTest(APITestCase):
    ''' Tests UPDATE video instances '''

    def setUp(self):
        helper = TestHelper()

        self.creator = helper.create_user()
        self.video = helper.upload_video(self.creator, is_public=False)
        self.noncreator = helper.create_user()
        self.video_file = helper.create_mp4_file(100)
        self.admin = helper.create_user(is_staff=True)
        self.url = 'video-detail'

    def test_patch_video_name_as_creator(self):
        ''' Should be allowed to change the name of your own video '''
        self.client.force_authenticate(user=self.creator)
        new_name = 'changed'
        response = self.client.patch(
                reverse(self.url, args=[self.video.id]),
                {'video_name': new_name}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.video_name, new_name)
    
    def test_patch_video_description_as_creator(self):
        ''' Should be allowed to change the description of your own video '''
        self.client.force_authenticate(user=self.creator)
        new_desc = 'new description'
        response = self.client.patch(
                reverse(self.url, args=[self.video.id]),
                {'description': new_desc}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.description, new_desc)
    
    def test_patch_video_visibility_as_creator(self):
        ''' Should be able to change if video is public/private on your own video '''
        self.client.force_authenticate(user=self.creator)
        is_public = True
        response = self.client.patch(
                reverse(self.url, args=[self.video.id]),
                {'is_public': is_public}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.is_public, is_public)

    def test_patch_video_file_as_creator(self):
        ''' Should not be able to change the video file once uploaded '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.patch(
                reverse(self.url, args=[self.video.id]),
                {'video': self.video_file}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_video_as_noncreator(self):
        ''' Should not be able to edit someone else's video if you're not admin '''
        response = self.client.patch(
                reverse(self.url, args=[self.video.id]),
                {'video_name': 'changed'}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.noncreator)
        response = self.client.patch(
                reverse(self.url, args=[self.video.id]),
                {'video_name': 'changed'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_video_as_admin(self):
        ''' Should be able to edit anyone's video '''
        self.client.force_authenticate(user=self.admin)
        new_name = 'changed'
        response = self.client.patch(
                reverse(self.url, args=[self.video.id]),
                {'video_name': new_name}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.video_name, new_name)

    def test_put_video(self):
        ''' PUT should be disabled on the view (as the video file cannot be resubmitted) '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.put(
                reverse(self.url, args=[self.video.id]),
                {'video_name': 'changed'}
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def tearDown(self):
        shutil.rmtree(
                config('VIDEO_STORAGE_TEST'),
                ignore_errors=True
        )

@override_settings(MEDIA_ROOT=config('VIDEO_STORAGE_TEST'))
class DeleteVideoTest(APITestCase):
    ''' Tests DELETE video instances ''' 

    def setUp(self):
        helper = TestHelper()

        self.creator = helper.create_user()
        self.video = helper.upload_video(self.creator, is_public=False)
        self.noncreator = helper.create_user()
        self.admin = helper.create_user(is_staff=True)
        self.url = 'video-detail'

    def test_delete_video_as_creator(self):
        ''' Should be able to delete your own video '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.delete(
                reverse(self.url, args=[self.video.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_video_as_noncreator(self):
        ''' Should not be able to delete a video that is not yours '''
        # Anonymous user
        response = self.client.delete(
                reverse(self.url, args=[self.video.id])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Noncreator user
        self.client.force_authenticate(user=self.noncreator)
        response = self.client.delete(
                reverse(self.url, args=[self.video.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_video_as_admin(self):
        ''' Should be able to delete anyone's video '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
                reverse(self.url, args=[self.video.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_nonexistent_video(self):
        ''' Should return a 404 '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.delete(
                reverse(self.url, args=[999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def tearDown(self):
        shutil.rmtree(
                config('VIDEO_STORAGE_TEST'),
                ignore_errors=True
        )
