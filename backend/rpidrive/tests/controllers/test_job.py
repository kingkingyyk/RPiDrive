from django.contrib.auth.models import User
from django.test import TestCase

from rpidrive.controllers.job import (
    JobNotFoundException,
    get_job,
    get_jobs,
)
from rpidrive.controllers.volume import (
    VolumePermissionEnum,
    VolumePermissionModel,
    update_volume_permission,
)
from rpidrive.models import Job, JobKind, JobStatus
from rpidrive.tests.helpers.setup import SetupContext


class TestJob(TestCase):
    """Test job controller"""

    def setUp(self):
        self.context = SetupContext()

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()
        Job.objects.all().delete()

    def test_get_jobs_1(self):
        """Test get_jobs"""
        job_1 = Job.objects.create(
            kind=JobKind.INDEX,
            description="example",
            data={},
            status=JobStatus.IN_QUEUE,
        )
        job_2 = Job.objects.create(
            kind=JobKind.INDEX,
            description="example2",
            data={},
            status=JobStatus.IN_QUEUE,
            volume=self.context.volume,
        )
        jobs = set(get_jobs(self.context.admin).all())
        self.assertEqual({job_1, job_2}, jobs)

    def test_get_jobs_2(self):
        """Test get_jobs (Normal user)"""
        Job.objects.create(
            kind=JobKind.INDEX,
            description="example",
            data={},
            status=JobStatus.IN_QUEUE,
        )
        job_2 = Job.objects.create(
            kind=JobKind.INDEX,
            description="example2",
            data={},
            status=JobStatus.IN_QUEUE,
            volume=self.context.volume,
        )

        normal_user = User.objects.create_user("normal")
        self.assertEqual(0, get_jobs(normal_user).count())

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=normal_user.id,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        self.assertEqual({job_2}, set(get_jobs(normal_user).all()))

    def test_get_job_1(self):
        """Test get_job"""
        job = Job.objects.create(
            kind=JobKind.INDEX,
            description="example",
            data={},
            status=JobStatus.IN_QUEUE,
        )
        job_2 = get_job(job.id)
        self.assertEqual(job, job_2)

    def test_get_job_2(self):
        """Test get_job (Invalid id)"""
        with self.assertRaises(JobNotFoundException):
            get_job(9999999)
