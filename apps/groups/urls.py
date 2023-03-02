from django.urls import path, include
from apps.groups.views import GroupViewSet, GroupJoinView, GroupLeaveView, GroupInviteView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'groups', GroupViewSet, basename='group')
urlpatterns = [
        path('', include(router.urls)),
        path('groups/<int:group_id>/join', GroupJoinView.as_view(), name='join'),
        path('groups/<int:group_id>/leave', GroupLeaveView.as_view(), name='leave'),
        path('groups/<int:group_id>/invite', GroupInviteView.as_view(), name='invite')
]
