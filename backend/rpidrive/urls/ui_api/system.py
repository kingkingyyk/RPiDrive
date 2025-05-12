from django.urls import path

from rpidrive.views.ui_api.system import (
    SystemDetailView,
    SystemNetworkView,
)

urlpatterns = [
    path("details", SystemDetailView.as_view()),
    path("network", SystemNetworkView.as_view()),
]
