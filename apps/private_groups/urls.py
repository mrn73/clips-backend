from django.urls import path
from apps.private_groups.views import PrivateGroupListView, PrivateGroupDetailView

urlpatterns = [
        path('users/<int:user_id>/private-groups/', 
             PrivateGroupListView.as_view(), 
             name='user-private-groups'
        ),
        path('private-groups/<int:pk>/',
             PrivateGroupDetailView.as_view(),
             name='private-group-detail'
        )
]
