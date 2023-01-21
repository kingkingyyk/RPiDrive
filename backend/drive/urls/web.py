from django.urls import path, re_path
from drive.views.web import (
    create_storage_provider,
    create_playlist,
    create_user,
    generate_quick_access_link,
    get_current_user,
    get_network_info,
    get_playlists,
    get_storage_provider_types,
    get_storage_provider_permissions,
    get_storage_providers,
    get_system_info,
    get_users,
    initialize_system,
    is_logged_in,
    get_jobs,
    manage_file,
    manage_playlist,
    manage_storage_provider,
    manage_user,
    move_files,
    perform_index,
    search_file,
    user_login,
    user_logout,
    zip_files,
)
from rpidrive.views import page_not_found

urlpatterns = [
    # Storage Provider
    path(
        r'storage-provider-types',
        get_storage_provider_types,
        name='storage_provider.list_types',
    ),
    path(
        r'storage-provider-permissions',
        get_storage_provider_permissions,
        name='storage-provider.list_permissions',
    ),
    path(
        r'storage-providers',
        get_storage_providers,
        name='storage-provider.list',
    ),
    path(
        r'storage-providers/create',
        create_storage_provider,
        name='storage-provider.create',
    ),
    path(
        r'storage-providers/<int:provider_id>/index',
        perform_index,
        name='storage-provider.index',
    ),
    path(
        r'storage-providers/<int:provider_id>',
        manage_storage_provider,
        name='storage-provider.manage',
    ),

    # Files
    path(r'files/search', search_file, name='file.search'),
    path(r'files/move', move_files, name='file.move'),
    path(r'files/zip', zip_files, name='file.zip'),
    path(
        r'files/<str:file_id>/quick-access',
        generate_quick_access_link,
        name='file.quick-access',
    ),
    path(r'files/<str:file_id>', manage_file, name='file.manage'),

    # Jobs
    path(r'jobs', get_jobs, name='job.list'),

    # Playlists
    path(r'playlists', get_playlists, name='playlist.list'),
    path(r'playlists/create', create_playlist, name='playlist.create'),
    path(r'playlists/<str:playlist_id>', manage_playlist, name='playlist.manage'),

    # System
    path(
        r'system/initialize',
        initialize_system,
        name='system.initialize'
    ),
    path(
        r'system/network-usage',
        get_network_info,
        name='system.network_usage'
    ),
    path(r'system/info', get_system_info, name='system.info'),

    # Users
    path(r'users/create', create_user, name='user.create'),
    path(r'users/current', get_current_user, name='user.get'),
    path(r'users/<int:user_id>', manage_user, name='user.manage'),
    path(r'users', get_users, name='user.list'),
    path(r'auth/login', user_login, name='user.login'),
    path(r'auth/logout', user_logout, name='user.logout'),
    path(r'auth/logged-in', is_logged_in, name='user.is_logged_in'),

    # Invalid URLs
    re_path(r'^(?P<path>.*)/$', page_not_found),
    re_path(r'$', page_not_found),
]
