from django.urls import path, include
from .views import views_file, views_system, views_downloader, views_user_accounts

urlpatterns = [
    path(r'download/<file_id>', views_file.download),

    path(r'angular-api/folder-redirect/<folder_id>', views_file.get_folder_redirect),
    path(r'angular-api/child-files/', views_file.get_child_files),
    path(r'angular-api/child-folders/', views_file.get_child_folders),
    path(r'angular-api/child-filenames/', views_file.get_child_filenames),
    path(r'angular-api/storages', views_file.get_storages),

    path(r'angular-api/create-new-folder', views_file.create_new_folder),
    path(r'angular-api/upload-files/<folder_id>', views_file.upload_file),
    path(r'angular-api/rename-file/<file_id>', views_file.rename_file),
    path(r'angular-api/delete-files', views_file.delete_files),
    path(r'angular-api/move-files/<folder_id>', views_file.move_files),

    path(r'angular-api/download/add/url', views_downloader.add_url_download),
    path(r'angular-api/download/add/magnet', views_downloader.add_magnet_download),
    path(r'angular-api/download/add/torrent', views_downloader.add_url_download),
    path(r'angular-api/download/list', views_downloader.get_downloads),
    path(r'angular-api/download/<gid>/resume', views_downloader.resume_download),
    path(r'angular-api/download/<gid>/pause', views_downloader.pause_download),
    path(r'angular-api/download/<gid>/cancel', views_downloader.cancel_download),

    path(r'angular-api/user/login', views_user_accounts.login),
    path(r'angular-api/user/logout', views_user_accounts.logout),
    path(r'angular-api/user/current', views_user_accounts.current_user),
    path(r'angular-api/users', views_user_accounts.list_users),
    path(r'angular-api/user/create', views_user_accounts.create_user),
    path(r'angular-api/user/<user_id>/manage', views_user_accounts.manage_user),

    path(r'angular-api/system-facts', views_system.get_facts),
    path(r'angular-api/network-facts', views_system.get_network_facts),
]