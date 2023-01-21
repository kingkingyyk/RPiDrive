from django.http.response import JsonResponse
from django.views.decorators.http import require_GET

from drive.models import Job
from drive.views.web.shared import login_required_401

@login_required_401
@require_GET
def get_jobs(request):
    """Return jobs"""
    jobs = Job.objects.all()
    return JsonResponse(
        dict(
            values=[
                dict(
                    description=job.description,
                    progress_info=job.progress_info,
                    progress_value=job.progress_value,
                )
                for job in jobs
            ]
        )
    )
