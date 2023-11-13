from django.urls import path

from rpidrive.views.ui_api.files import (
    FileCompressView,
    FileDeleteView,
    FileDetailView,
    FileMoveView,
    FileRenameView,
    FileSearchView,
    FileShareView,
    FileThumbnailView,
    FileUploadView,
    NewFolderView,
)

urlpatterns = [
    path("compress", FileCompressView.as_view()),
    path("delete", FileDeleteView.as_view()),
    path("move", FileMoveView.as_view()),
    path("search", FileSearchView.as_view()),
    path("<uuid:file_id>", FileDetailView.as_view()),
    path("<uuid:file_id>/new-folder", NewFolderView.as_view()),
    path("<uuid:file_id>/rename", FileRenameView.as_view()),
    path("<uuid:file_id>/share", FileShareView.as_view()),
    path("<uuid:file_id>/thumbnail", FileThumbnailView.as_view()),
    path("<uuid:file_id>/upload", FileUploadView.as_view()),
]
