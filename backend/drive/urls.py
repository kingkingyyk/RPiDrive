from django.urls import path, include
from .views import views_file, views_system

urlpatterns = [
    path(r'download/<file_id>', views_file.download),

    path(r'angular-api/folder-redirect/<folder_id>', views_file.get_folder_redirect),
    path(r'angular-api/child-files/', views_file.get_child_files),
    path(r'angular-api/child-filenames/', views_file.get_child_filenames),
    path(r'angular-api/storages', views_file.get_storages),

    path(r'angular-api/create-new-folder', views_file.create_new_folder),
    path(r'angular-api/rename-file/<file_id>', views_file.rename_file),
    path(r'angular-api/delete-files', views_file.delete_files),
    path(r'angular-api/move-files', views_file.move_files),

    path(r'angular-api/system-facts', views_system.get_facts),
    path(r'angular-api/network-facts', views_system.get_network_facts),
]