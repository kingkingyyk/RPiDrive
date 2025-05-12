from django.contrib.auth.models import User
from django.db.models import Q, QuerySet

from rpidrive.controllers.exceptions import ObjectNotFoundException
from rpidrive.controllers.volume import get_volumes
from rpidrive.models import Job


class JobNotFoundException(ObjectNotFoundException):
    """Job not found exception"""


def get_jobs(user: User) -> QuerySet:
    """Get jobs by user"""
    volume_pks = list(get_volumes(user).values_list("pk", flat=True))
    filters = Q(volume_id__in=volume_pks)
    if user.is_superuser:
        filters |= Q(volume=None)
    return Job.objects.filter(filters)


def get_job(job_pk: int) -> Job:
    """Get job by id"""
    job = Job.objects.filter(pk=job_pk).first()
    if not job:
        raise JobNotFoundException("Job not found.")
    return job


def cancel_job(_user: User, _job_pk: int):
    """Cancel job"""
