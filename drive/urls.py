from django.urls import path
from drive.views import views, views_downloader, views_auth, views_maintenance

urlpatterns = [
    path('login', views_auth.login_view, name='login'),
    path('logout', views_auth.logout_view, name='logout'),

    path('', views.index, name='index'),
    path('ongoing-tasks', views.ongoing_tasks, name='ongoing_tasks'),
    path('navigate/<str:folder_id>', views.navigate, name='navigate'),
    path('download/<str:file_id>', views.download, name='download'),
    path('upload/<str:folder_id>', views.upload_files, name='upload'),
    path('create-folder/<str:folder_id>', views.create_folder, name='create_folder'),
    path('rename/<str:file_obj_id>', views.rename_file_object, name='rename_file_obj'),
    path('move', views.move_file_object, name='move_file_objects'),
    path('delete', views.delete_file_objects, name='delete_file_objects'),
    path('list-folders/<str:folder_id>', views.list_folders, name='list_folders'),
    path('search-hint', views.search_hint, name='search_hint'),
    path('search', views.search, name='search'),

    path('downloads', views_downloader.list, name='downloads'),
    path('downloader/add', views_downloader.add, name='downloader_add'),
    path('downloader/cancel', views_downloader.cancel, name='downloader_cancel'),

    path('storage', views_maintenance.manage_storage, name='manage_storage'),
    path('system-status', views_maintenance.system_status, name='system_status'),
    path('system-status/update', views_maintenance.system_status_update, name='system_status_update'),
]
