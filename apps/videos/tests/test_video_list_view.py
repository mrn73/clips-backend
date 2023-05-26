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
This module provides tests for creating and listing videos.

Classes:
    - GetAllVideoTest: Provides methods to test GET on video-list endpoint.
    - CreateVideoTest: Provides methods to test POST on video-list endpoint.

Settings Override:
    For these tests, we need to override the settings so that videos are stored
    in a separate folder from the actual uploads. This makes it easier to clean
    up any files created while testing.

TODO:
    Possibly use setUpTestData() rather than setUp() so that video files are
    created once for the class and not before each function call. This would
    most likely drastically improve runtime.
    As of now I can't get setUpTestData() working with the APITestCase class.
'''
@override_settings(MEDIA_ROOT=config('VIDEO_STORAGE_TEST'))
class GetAllVideosTest(APITestCase):
    ''' Tests GET all videos '''

    def setUp(self):
        helper = TestHelper()

        # Users
        self.admin = helper.create_user(is_staff=True)
        self.user = helper.create_user()
        self.shared_user = helper.create_user()
        
        # Videos
        self.private_video = helper.upload_video(creator=self.user, is_public=False)
        self.public_video = helper.upload_video(creator=self.user)
        self.shared_video = helper.upload_video(creator=self.user, is_public=False) 
        self.random_video = helper.upload_video() 

        helper.share_video_with_user(self.shared_video, self.shared_user)
        self.url = 'user-videos'

    def test_get_all_videos_as_admin(self):
        ''' Should return all videos of the user '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # should see all videos created by the user
        query = Video.objects.filter(creator=self.user)
        self.assertEqual(len(response.data), len(query))

    def test_get_all_videos_as_user(self):
        ''' Should return all videos of the user '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # should see all videos created by themself
        query = Video.objects.filter(creator=self.user)
        self.assertEqual(len(response.data), len(query))

    def test_get_all_as_videos_shared_user(self):
        ''' Should return all public videos or any videos that are explicitly shared '''
        self.client.force_authenticate(user=self.shared_user)
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # should only see shared and public videos under the user
        query = Video.objects.filter(
                Q(creator=self.user) &
                Q(is_public=True) | Q(shared_with__user=self.shared_user)
        )
        self.assertEqual(len(response.data), len(query))

    def test_get_all_videos_as_anonymous(self):
        ''' Should return all public videos '''
        response = self.client.get(reverse(self.url, args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # should only see the public video under the user
        self.assertEqual(len(response.data), 1)

    def tearDown(self):
        shutil.rmtree(
                config('VIDEO_STORAGE_TEST'),
                ignore_errors=True
        )
        
@override_settings(MEDIA_ROOT=config('VIDEO_STORAGE_TEST'))
class CreateVideoTest(APITestCase):
    ''' Tests POST Video instances '''

    def setUp(self):
        helper = TestHelper()

        self.user = helper.create_user()
        self.shared_users = [helper.create_user() for i in range(3)]
        shared_users_urls = list(map(
                lambda user: reverse('user-detail', args=[user.id]),
                self.shared_users
        ))
        
        real_video_file = helper.create_mp4_file(1024)

        self.valid_payload = {
                'video_name': 'test',
                'video': real_video_file
        }

        self.shared_users_payload = {
                'video_name': 'test',
                'video': real_video_file,
                'is_public': False,
                'shared_with': shared_users_urls
        }

        # Missing required 'video_name'
        self.no_name_payload = {
                'video': real_video_file
        }

        # Missing video file
        self.no_video_payload = {
                'video_name': 'test'
        }

        # Video file's content will be missing mp4 signature 
        self.fake_video_payload = {
                'video_name': 'test',
                'video': helper.create_file(100)
        }

        # This file will be over the 1GB maximum
        self.large_video_payload = {
                'video_name': 'test',
                'video': helper.create_mp4_file(1024**3 + 1)
        }

        self.url = 'user-videos'

    def test_create_video_as_authenticated_no_shared_list(self):
        ''' Logged-in users should be able to upload video '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_video_as_unauthenticated(self):
        ''' Signed-out users should not have permission to upload videos '''
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_private_video_with_shared_users(self):
        ''' Should successfully share the video with every user in the request '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.shared_users_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)        

        # Ensure that the video was properly shared
        self.assertEqual(
                len(Shared.objects.all()),
                len(self.shared_users)
        )

    def test_create_public_video_with_shared_users(self):
        ''' Should not share the video with anyone when the video is public '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                {**self.shared_users_payload, **{'is_public': True}}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)        

        # Ensure that the video wasn't shared, since the video is public.
        self.assertEqual(
                len(Shared.objects.all()),
                0
        )

    def test_create_video_with_no_name(self):
        ''' Should fail serialization: 'video_name' required '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.no_name_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_video_with_no_video_file(self):
        ''' Should fail serialization: 'video' required '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.no_video_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_video_non_mp4_file(self):
        ''' Should fail serialization: file signature must be mp4 '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.fake_video_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_video_with_insufficient_space(self):
        ''' Should fail to upload the video size exceeds remaining space'''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.large_video_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_video_too_large(self):
        ''' Should fail to upload any video larger than 1GB '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse(self.url, args=[self.user.id]),
                self.large_video_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        shutil.rmtree(
                config('VIDEO_STORAGE_TEST'),
                ignore_errors=True
        )
