from django.urls import path

from rpidrive.views.ui_api.playlists import (
    PlaylistCreateView,
    PlaylistDetailView,
    PlaylistListView,
)

urlpatterns = [
    path("", PlaylistListView.as_view()),
    path("create", PlaylistCreateView.as_view()),
    path("<str:playlist_id>", PlaylistDetailView.as_view()),
]
