from django.urls import include, path

from rpidrive.views.ui_api.files.download_view import FileDownloadView
from rpidrive.views.ui_api.files.qa_view import FileQAView

urlpatterns = [
    path("ui-api/", include("rpidrive.urls.ui_api")),
    path("download/<str:file_id>", FileDownloadView.as_view()),
    path("quick-access", FileQAView.as_view()),
]
