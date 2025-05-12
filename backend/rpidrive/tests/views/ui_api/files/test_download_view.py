import http
import os
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files.download_view import FileDownloadView


class TestFileDownloadView(TestCase):
    """Test FileDownloadView"""

    def setUp(self):
        self.base_url = "/drive/download/"
        self.url = f"{self.base_url}{uuid.uuid4()}"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileDownloadView, resolve(self.url).func.view_class)

    def test_get_1(self):
        """Test GET method"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("abcdefghijk")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)
        file_url = f"{self.base_url}{file_1_obj.id}"

        self.client.force_login(self.context.admin)
        response = self.client.get(file_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(b"abcdefghijk", b"".join(response.streaming_content))
        self.assertEqual("application/octet-stream", response.headers["Content-Type"])
        self.assertEqual("11", response.headers["Content-Length"])
        self.assertEqual(
            'attachment;filename="song1.m4a"', response.headers["Content-Disposition"]
        )

        response = self.client.get(file_url, headers={"Range": "bytes=2-5"})
        self.assertEqual(http.HTTPStatus.PARTIAL_CONTENT, response.status_code)
        self.assertEqual(b"cdef", b"".join(response.streaming_content))
        self.assertEqual("application/octet-stream", response.headers["Content-Type"])
        self.assertEqual("4", response.headers["Content-Length"])
        self.assertEqual(
            'attachment;filename="song1.m4a"', response.headers["Content-Disposition"]
        )

    def test_get_2(self):
        """Test GET method (Non-admin user)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)
        file_url = f"{self.base_url}{file_1_obj.id}"

        self.client.force_login(self.user)
        response = self.client.get(file_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )
        response = self.client.get(file_url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(b"a", b"".join(response.streaming_content))

    def test_get_3(self):
        """Test GET method (Invalid file id)"""
        file_url = f"{self.base_url}{uuid.uuid4()}"
        self.client.force_login(self.context.admin)
        response = self.client.get(file_url)
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

    def test_get_4(self):
        """Test GET method (Folder)"""
        file_url = f"{self.base_url}{self.context.root_file.id}"
        self.client.force_login(self.context.admin)
        response = self.client.get(file_url)
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Can't download folder."}, response.json())

    def test_get_5(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_1(self):
        """Test POST method"""
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_2(self):
        """Test POST method"""
        response = self.client.post(self.url)
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
