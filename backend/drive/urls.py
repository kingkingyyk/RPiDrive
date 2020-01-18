from django.urls import path, include
from . import views

urlpatterns = [
    path(r'angular-api/child-files/', views.get_child_files),
    path(r'angular-api/storages', views.get_storages),
    path(r'angular-api/download/<file_id>', views.download),
    path(r'angular-api/create-new-folder/<folder_id>', views.create_new_folder)
]