from django.urls import path, include
from drive.views.web import *

urlpatterns = [
    path(r'storage-provider-types', get_storage_provider_types),
    path(r'storage-provider-permissions', get_storage_provider_permissions),

    path(r'storage-providers', get_storage_providers),
    path(r'storage-providers/create', create_storage_provider),
    path(r'storage-providers/<int:provider_id>/index', perform_index),
    path(r'storage-providers/<int:provider_id>', manage_storage_provider),

    path(r'files/search', search_file),
    path(r'files/<str:file_id>', manage_file),

    path(r'playlists', get_playlists),
    path(r'playlists/create', create_playlist),
    path(r'playlists/<str:playlist_id>', manage_playlist),

    path(r'system/initialize', initialize_system),
    path(r'system/network-usage', get_network_info),
    path(r'system/info', get_system_info),

    path(r'users/create', create_user),
    path(r'users/current', get_current_user),
    path(r'users/<int:user_id>', manage_user),
    path(r'users', get_users),

    path(r'auth/login', user_login),
    path(r'auth/logout', user_logout),
    path(r'auth/logged-in', is_logged_in),
]