from django.urls import path, include
from drive.views.web import *

urlpatterns = [
    path(r'storage-provider-types', get_storage_provider_types),

    path(r'storage-providers', get_storage_providers),
    path(r'storage-providers/create', create_storage_provider),
    path(r'storage-providers/<int:provider_id>/index', perform_index),
    path(r'storage-providers/<int:provider_id>', manage_storage_provider),

    path(r'files/create', create_file),
    path(r'files/<str:file_id>/move', move_file),
    path(r'files/<str:file_id>', manage_file),
]