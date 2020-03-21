from django.urls import path, include
from .views import *

urlpatterns = [
    path(r'angular-api/playlists', get_playlists),
    path(r'angular-api/playlists/search', search_playlists),
    path(r'angular-api/playlist/create', create_playlist),
    path(r'angular-api/playlist/<playlist_id>', manage_playlist),
    path(r'angular-api/media/search', search_media),
]