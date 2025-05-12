import http
import os
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import Job, JobKind, JobStatus, VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files import FileCompressView


class TestFileCompressView(TestCase):
    """Test FileCompressView"""

    def setUp(self):
        self.url = "/drive/ui-api/files/compress"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileCompressView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {
            "files": [str(file_1_obj.id)],
            "compress_dir": str(self.context.root_file.id),
            "compress_name": "hehe.zip",
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.assertEqual(1, Job.objects.count())
        job = Job.objects.first()
        self.assertEqual(JobKind.ZIP, job.kind)
        self.assertEqual(self.context.volume, job.volume)
        self.assertEqual("hehe.zip", job.description)
        self.assertEqual(
            {
                "name": "hehe.zip",
                "files": [str(file_1_obj.id)],
                "parent": str(self.context.root_file.id),
            },
            job.data,
        )
        self.assertEqual(JobStatus.IN_QUEUE, job.status)
        self.assertEqual(0, job.progress)
        self.assertEqual(False, job.to_stop)

    def test_post_2(self):
        """Test POST method (Invalid name)"""
        post_data = {
            "files": [str(uuid.uuid4())],
            "compress_dir": str(self.context.root_file.id),
            "compress_name": "  ",
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Invalid file name."}, response.json())
        self.assertEqual(0, Job.objects.count())

    def test_post_3(self):
        """Test POST method (No permission)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {
            "files": [str(file_1_obj.id)],
            "compress_dir": str(self.context.root_file.id),
            "compress_name": "hehe.zip",
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Volume not found."}, response.json())
        self.assertEqual(0, Job.objects.count())

    def test_post_4(self):
        """Test POST method (Invalid parent folder)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {
            "files": [str(file_1_obj.id)],
            "compress_dir": str(uuid.uuid4()),
            "compress_name": "hehe.zip",
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())
        self.assertEqual(0, Job.objects.count())

    def test_post_5(self):
        """Test POST method (Invalid file list)"""
        post_data = {
            "files": [str(uuid.uuid4())],
            "compress_dir": str(self.context.root_file.id),
            "compress_name": "hehe.zip",
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Invalid file to compress."}, response.json())
        self.assertEqual(0, Job.objects.count())

    def test_post_6(self):
        """Test POST method (Empty file list)"""
        post_data = {
            "files": [],
            "compress_dir": str(self.context.root_file.id),
            "compress_name": "hehe.zip",
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "No file to compress."}, response.json())
        self.assertEqual(0, Job.objects.count())

    def test_post_7(self):
        """Test POST method (No login)"""
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_8(self):
        """Test POST method (Auto strip name)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {
            "files": [str(file_1_obj.id)],
            "compress_dir": str(self.context.root_file.id),
            "compress_name": " hehe.zip ",
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.assertEqual(1, Job.objects.count())
        job = Job.objects.first()
        self.assertEqual(JobKind.ZIP, job.kind)
        self.assertEqual(self.context.volume, job.volume)
        self.assertEqual("hehe.zip", job.description)
        self.assertEqual(
            {
                "name": "hehe.zip",
                "files": [str(file_1_obj.id)],
                "parent": str(self.context.root_file.id),
            },
            job.data,
        )

    def test_post_9(self):
        """Test POST method (Auto append .zip)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {
            "files": [str(file_1_obj.id)],
            "compress_dir": str(self.context.root_file.id),
            "compress_name": "hehe",
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.assertEqual(1, Job.objects.count())
        job = Job.objects.first()
        self.assertEqual(JobKind.ZIP, job.kind)
        self.assertEqual(self.context.volume, job.volume)
        self.assertEqual("hehe.zip", job.description)
        self.assertEqual(
            {
                "name": "hehe.zip",
                "files": [str(file_1_obj.id)],
                "parent": str(self.context.root_file.id),
            },
            job.data,
        )

    def test_post_10(self):
        """Test POST method (Read only user)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        post_data = {
            "files": [str(file_1_obj.id)],
            "compress_dir": str(self.context.root_file.id),
            "compress_name": "hehe.zip",
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertEqual(0, Job.objects.count())

    def test_get_1(self):
        """Test GET method"""
        self.client.force_login(self.context.admin)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_2(self):
        """Test GET method"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_1(self):
        """Test PUT method"""
        self.client.force_login(self.context.admin)
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_2(self):
        """Test PUT method"""
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_1(self):
        """Test DELETE method"""
        self.client.force_login(self.context.admin)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_2(self):
        """Test DELETE method"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
