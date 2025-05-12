from django.urls import path

from rpidrive.views.ui_api.jobs import (
    JobCancelView,
    JobListView,
)

urlpatterns = [
    path("", JobListView.as_view()),
    path("<int:job_id>/cancel", JobCancelView.as_view()),
]
