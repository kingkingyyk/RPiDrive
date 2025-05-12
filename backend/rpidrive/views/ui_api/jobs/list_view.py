from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.job import get_jobs


class JobListView(LoginRequiredMixin, View):
    """Job list view"""

    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET response"""
        jobs = get_jobs(request.user).order_by("pk").all()
        return JsonResponse(
            {
                "values": [
                    {
                        "id": job.pk,
                        "description": job.description,
                        "progress": job.progress,
                        "status": job.status,
                        "to_stop": job.to_stop,
                        "kind": job.kind,
                    }
                    for job in jobs
                ]
            }
        )
