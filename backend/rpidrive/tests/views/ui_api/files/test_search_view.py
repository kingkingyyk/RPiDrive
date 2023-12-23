import http
import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.local_file import create_entry
from rpidrive.controllers.volume import VolumePermissionModel, update_volume_permission
from rpidrive.models import VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.files import FileSearchView


class TestSearchView(TestCase):
    """Test FileSearchView"""

    def setUp(self):
        self.context = SetupContext()
        self.url = "/drive/ui-api/files/search"
        self.user = User.objects.create_user("z")

    def tearDown(self):
        self.context.cleanup()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(FileSearchView, resolve(self.url).func.view_class)

    def test_get_1(self):
        """Test GET method"""
        folder_path = os.path.join(self.context.root_path, "dummy1")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )

        f_p = os.path.join(folder_path, "dummy2.m4a")
        with open(f_p, "w+") as f_h:
            f_h.write("a")
        file_obj = create_entry(self.context.volume, folder_obj, f_p)

        result = [file_obj, folder_obj]
        path = [f_p, folder_path]
        self.client.force_login(self.context.admin)
        response = self.client.get(self.url, {"keyword": "mmy"})
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        expected = {
            "values": [
                {
                    "id": str(x.id),
                    "name": x.name,
                    "path": path[idx],
                    "size": x.size,
                    "media_type": x.media_type,
                    "kind": x.kind.value,
                }
                for idx, x in enumerate(result)
            ]
        }
        actual = response.json()
        for row in actual["values"]:
            self.assertIsNotNone(row["last_modified"])
            del row["last_modified"]
        self.assertEqual(expected, response.json())

    def test_get_2(self):
        """Test GET method (No keyword)"""
        self.client.force_login(self.context.admin)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Missing keyword."}, response.json())

    def test_get_3(self):
        """Test GET method (Non-admin user)"""
        folder_path = os.path.join(self.context.root_path, "dummy1")
        os.makedirs(folder_path)
        folder_obj = create_entry(
            self.context.volume, self.context.root_file, folder_path
        )

        f_p = os.path.join(folder_path, "dummy2.m4a")
        with open(f_p, "w+") as f_h:
            f_h.write("a")
        create_entry(self.context.volume, folder_obj, f_p)

        self.client.force_login(self.user)
        response = self.client.get(self.url, {"keyword": "mmy"})
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"values": []}, response.json())

        update_volume_permission(
            self.context.admin,
            self.context.volume.id,
            [
                VolumePermissionModel(
                    user=self.user.id, permission=VolumePermissionEnum.READ
                )
            ],
        )
        response = self.client.get(self.url, {"keyword": "mmy"})
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(2, len(response.json()["values"]))

    def test_get_4(self):
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
        """Test POST method (No login)"""
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
        """Test PUT method (No login)"""
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
        """Test DELETE method (No login)"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
