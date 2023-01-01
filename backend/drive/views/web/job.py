from django.http.response import JsonResponse
from drive.models import Job

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
