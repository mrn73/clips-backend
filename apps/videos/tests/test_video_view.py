from rest_framework import status
from rest_framework.test import APITestCase
from utils.test_helper import TestHelper
from django.urls import reverse
from apps.videos.serializers import VideoSerializer
from apps.videos.models import Video
from django.db.models import Q

'''
This module provides tests for each available HTTP method on the Group model.

Classes:
    - GetAllVideoTest: Provides methods to test GET on video-list endpoint.
    - GetSingleVideoTest: Prodives methods to test GET on video-detail endpoint.
    - CreateVideoTest: Provides methods to test POST on video-list endpoint.
    - UpdateVideoTest: Provides methods to test PUT/PATCH on video-detail endpoint.
    - DeleteVideoTest: Provides methods to test DELETE on video-detail endpoint.
'''
class GetAllVideosTest(APITestCase):
    ''' Tests GET all videos '''

    def setUp(self):
        helper = TestHelper()
        self.admin = helper.create_user(is_staff=True)
        self.user = helper.create_user()
        self.user_video = helper.upload_video(creator=self.user)
        self.public_video = helper.upload_video()
        self.private_video = helper.upload_video(is_public=False) 

    def test_get_all_videos_as_admin(self):
        ''' Should return all videos '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('video-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = VideoSerializer(Video.objects.all(), many=True)
        self.assertEqual(response.data, serializer.data)

    def test_get_all_videos_as_user(self):
        ''' Should return all public videos or videos shared with the user '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('video-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # filter by is_public OR creator is self
        query = Video.objects.filter(Q(is_public=True) | Q(creator=self.user))
        serializer = VideoSerializer(query, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_get_all_videos_as_anonymous(self):
        ''' Should return all public videos '''
        response = self.client.get(reverse('video-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # filter by is_public
        query = Video.objects.filter(is_public=True)
        serializer = VideoSerializer(query, many=True)
        self.assertEqual(response.data, serializer.data)

class GetSingleVideoTest(APITestCase):
    ''' Tests GET single Video instances '''

    def setUp(self):
        helper = TestHelper()

        self.admin = helper.create_user(is_staff=True)
        self.user = helper.create_user()
        self.user_video = helper.upload_video(creator=self.user)
        self.public_video = helper.upload_video()
        self.private_video = helper.upload_video(is_public=False)  

    def test_get_unshared_video_as_admin(self):
        ''' Should always be able to see any video '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('video-detail', args=[self.public_video.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_video_as_creator(self):
        ''' The creator can always see their own video '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('video-detail', args=[self.user_video.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_shared_video_as_user(self):
        ''' A user should be able to see a video shared in their group '''
        # May be reworking how groups work so skip for now.
        pass

    def test_get_unshared_video_as_user(self):
        ''' A user cannot see a private video not shared with them '''
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('video-detail', args=[self.private_video.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_public_video(self):
        ''' Any (including anonymous) user should be able to see a public video '''
        response = self.client.get(reverse('video-detail', args=[self.public_video.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
class CreateVideoTest(APITestCase):
    ''' Tests POST Video instances '''

    def setUp(self):
        helper = TestHelper()

        self.user = helper.create_user()
        
        real_video_file = helper.create_mp4_file(1024)

        self.valid_payload = {
                'video_name': 'test',
                'video': real_video_file
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

    def test_create_video_as_authenticated(self):
        ''' Logged-in users should be able to upload video '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse('video-list'),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_video_as_unauthenitcated(self):
        ''' Signed-out users should not have permission to upload videos '''
        response = self.client.post(
                reverse('video-list'),
                self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_video_with_no_name(self):
        ''' Should fail serialization: 'video_name' required '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse('video-list'),
                self.no_name_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_video_with_no_video_file(self):
        ''' Should fail serialization: 'video' required '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse('video-list'),
                self.no_video_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_video_non_mp4_file(self):
        ''' Should fail serialization: file signature must be mp4 '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse('video-list'),
                self.fake_video_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_video_with_insufficient_space(self):
        ''' Should fail to upload the video size exceeds remaining space'''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse('video-list'),
                self.large_video_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_video_too_large(self):
        ''' Should fail to upload any video larger than 1GB '''
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
                reverse('video-list'),
                self.large_video_payload
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UpdateVideoTest(APITestCase):
    ''' Tests UPDATE video instances '''

    def setUp(self):
        helper = TestHelper()

        self.creator = helper.create_user()
        self.video = helper.upload_video(self.creator, is_public=False)
        self.noncreator = helper.create_user()
        self.video_file = helper.create_mp4_file(100)
        self.admin = helper.create_user(is_staff=True)

    def test_creator_patch_video_name(self):
        ''' Should be allowed to change the name of your own video '''
        self.client.force_authenticate(user=self.creator)
        new_name = 'changed'
        response = self.client.patch(
                reverse('video-detail', args=[self.video.id]),
                {'video_name': new_name}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.video_name, new_name)
    
    def test_creator_patch_video_description(self):
        ''' Should be allowed to change the description of your own video '''
        self.client.force_authenticate(user=self.creator)
        new_desc = 'new description'
        response = self.client.patch(
                reverse('video-detail', args=[self.video.id]),
                {'description': new_desc}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.description, new_desc)
    
    def test_creator_patch_video_visibility(self):
        ''' Should be able to change if video is public/private on your own video '''
        self.client.force_authenticate(user=self.creator)
        is_public = True
        response = self.client.patch(
                reverse('video-detail', args=[self.video.id]),
                {'is_public': is_public}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.is_public, is_public)

    def test_creator_patch_video_file(self):
        ''' Should not be able to change the video file once uploaded '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.patch(
                reverse('video-detail', args=[self.video.id]),
                {'video': self.video_file}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_noncreator_patch_video(self):
        ''' Should not be able to edit someone else's video if you're not admin '''
        response = self.client.patch(
                reverse('video-detail', args=[self.video.id]),
                {'video_name': 'changed'}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.noncreator)
        response = self.client.patch(
                reverse('video-detail', args=[self.video.id]),
                {'video_name': 'changed'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_patch_video(self):
        ''' Should be able to edit anyone's video '''
        self.client.force_authenticate(user=self.admin)
        new_name = 'changed'
        response = self.client.patch(
                reverse('video-detail', args=[self.video.id]),
                {'video_name': new_name}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.video_name, new_name)

    def test_put_video(self):
        ''' PUT should be disabled on the view (as the video file cannot be resubmitted) '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.put(
                reverse('video-detail', args=[self.video.id]),
                {'video_name': 'changed'}
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class DeleteVideoTest(APITestCase):
    ''' Tests DELETE video instances ''' 

    def setUp(self):
        helper = TestHelper()

        self.creator = helper.create_user()
        self.video = helper.upload_video(self.creator, is_public=False)
        self.noncreator = helper.create_user()
        self.admin = helper.create_user(is_staff=True)

    def test_creator_delete_video(self):
        ''' Should be able to delete your own video '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.delete(
                reverse('video-detail', args=[self.video.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_noncreator_delete_video(self):
        ''' Should not be able to delete a video that is not yours '''
        # Anonymous user
        response = self.client.delete(
                reverse('video-detail', args=[self.video.id])
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Noncreator user
        self.client.force_authenticate(user=self.noncreator)
        response = self.client.delete(
                reverse('video-detail', args=[self.video.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_delete_video(self):
        ''' Should be able to delete anyone's video '''
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
                reverse('video-detail', args=[self.video.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_nonexistent_video(self):
        ''' Should return a 404 '''
        self.client.force_authenticate(user=self.creator)
        response = self.client.delete(
                reverse('video-detail', args=[999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
