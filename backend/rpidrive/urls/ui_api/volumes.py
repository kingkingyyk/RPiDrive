from django.urls import path

from rpidrive.views.ui_api.volumes import (
    VolumeCreateView,
    VolumeDetailView,
    VolumeIndexView,
    VolumeKindView,
    VolumeListView,
    VolumePermissionView,
)

urlpatterns = [
    path("", VolumeListView.as_view()),
    path("create", VolumeCreateView.as_view()),
    path("kinds", VolumeKindView.as_view()),
    path("permissions", VolumePermissionView.as_view()),
    path("<uuid:volume_id>", VolumeDetailView.as_view()),
    path("<uuid:volume_id>/index", VolumeIndexView.as_view()),
]
