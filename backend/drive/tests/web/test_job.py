import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from drive.models import Job

class TestJob(TestCase):
    """Test job views"""

    def setUp(self):
        self.url = reverse('job.list')
        self.user = User.objects.create_user(
            username='hello'
        )

        self.job_1 = Job.objects.create(
            task_type=Job.TaskTypes.INDEX,
            description='this is index job',
            data='this is data part',
            progress_value=12,
        )

        self.job_2 = Job.objects.create(
            task_type=Job.TaskTypes.INDEX,
            description='this is zip job',
            progress_info='info prog',
            progress_value=12,
        )

    def tearDown(self):
        Job.objects.all().delete()
        User.objects.all().delete()

    def test_get_jobs_url(self):
        """Test get_jobs url"""
        self.assertEqual('/drive/web-api/jobs', self.url)

    def test_get_jobs_methods(self):
        """Test get_jobs http methods"""
        # Not logged in
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_get_jobs(self):
        """Test get_jobs list"""
        # Not logged in
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.UNAUTHORIZED, response.status_code)

        # Logged in
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        expected_data = dict(
            values=[
                dict(
                    description=self.job_1.description,
                    progress_info=self.job_1.progress_info,
                    progress_value=self.job_1.progress_value,
                ),
                dict(
                    description=self.job_2.description,
                    progress_info=self.job_2.progress_info,
                    progress_value=self.job_2.progress_value,
                )
            ]
        )
        self.assertEqual(expected_data, response.json())
