from django.urls import include, path

urlpatterns = [
    path("files/", include("rpidrive.urls.ui_api.files")),
    path("jobs/", include("rpidrive.urls.ui_api.jobs")),
    path("users/", include("rpidrive.urls.ui_api.users")),
    path("volumes/", include("rpidrive.urls.ui_api.volumes")),
    path("system/", include("rpidrive.urls.ui_api.system")),
    path("playlists/", include("rpidrive.urls.ui_api.playlists")),
]
