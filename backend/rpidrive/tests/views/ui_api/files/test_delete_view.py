import http
import os
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import File, VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files import FileDeleteView


class TestFileDeleteView(TestCase):
    """Test FileDeleteView"""

    def setUp(self):
        self.url = "/drive/ui-api/files/delete"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileDeleteView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        fp_2 = os.path.join(self.context.root_path, "song2.m4a")
        with open(fp_2, "w+") as f_h:
            f_h.write("a")
        file_2_obj = create_entry(self.context.volume, self.context.root_file, fp_2)

        post_data = {
            "files": [str(file_1_obj.id)],
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({}, response.json())

        self.assertFalse(os.path.exists(fp_1))
        self.assertFalse(File.objects.filter(id=file_1_obj.id).exists())
        self.assertTrue(os.path.exists(fp_2))
        self.assertTrue(File.objects.filter(id=file_2_obj.id).exists())

    def test_post_2(self):
        """Test POST method (Invalid file id)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {
            "files": [str(file_1_obj.id), str(uuid.uuid4())],
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

        self.assertTrue(os.path.exists(fp_1))
        self.assertTrue(File.objects.filter(id=file_1_obj.id).exists())

    def test_post_3(self):
        """Test POST method (Empty file list)"""
        post_data = {
            "files": [],
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "File not found."}, response.json())

    def test_post_4(self):
        """Test POST method (Delete root file)"""
        post_data = {
            "files": [str(self.context.root_file.id)],
        }
        self.client.force_login(self.context.admin)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Can't delete root file."}, response.json())
        self.assertEqual(1, File.objects.count())
        self.assertTrue(os.path.exists(self.context.root_path))

    def test_post_5(self):
        """Test POST method (No permission)"""
        fp_1 = os.path.join(self.context.root_path, "song1.m4a")
        with open(fp_1, "w+") as f_h:
            f_h.write("a")
        file_1_obj = create_entry(self.context.volume, self.context.root_file, fp_1)

        post_data = {
            "files": [str(file_1_obj.id)],
        }
        self.client.force_login(self.user)
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Volume not found."}, response.json())

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertTrue(os.path.exists(fp_1))

    def test_post_6(self):
        """Test POST method (No login)"""
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

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
