import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.volume import (
    VolumePermissionModel,
    update_volume_permission,
)
from rpidrive.models import VolumePermissionEnum
from rpidrive.tests.helpers.setup import SetupContext
from rpidrive.views.ui_api.volumes import VolumeListView


class TestVolumeListView(TestCase):
    """Test VolumeListView"""

    def setUp(self):
        self.url = "/drive/ui-api/volumes/"
        self.context = SetupContext()
        self.user = User.objects.create_user("z")

    def tearDown(self):
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(VolumeListView, resolve(self.url).func.view_class)

    def test_get_1(self):
        """Test GET method"""
        expected = {
            "values": [
                {
                    "id": str(self.context.volume.id),
                    "name": self.context.volume.name,
                    "indexing": True,
                    "path": self.context.volume.path,
                }
            ]
        }
        self.client.force_login(self.context.admin)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)

        data = response.json()
        self.assertGreater(data["values"][0]["total_space"], 0)
        self.assertGreater(data["values"][0]["used_space"], 0)
        self.assertGreater(data["values"][0]["free_space"], 0)
        del data["values"][0]["total_space"]
        del data["values"][0]["used_space"]
        del data["values"][0]["free_space"]
        self.assertEqual(expected, data)

    def test_get_2(self):
        """Test GET method"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual({"values": []}, response.json())

        update_volume_permission(
            self.context.admin,
            str(self.context.volume.id),
            [
                VolumePermissionModel(
                    user=self.user.id,
                    permission=VolumePermissionEnum.READ,
                )
            ],
        )
        expected = {
            "values": [
                {
                    "id": str(self.context.volume.id),
                    "name": self.context.volume.name,
                    "indexing": True,
                    "path": self.context.volume.path,
                }
            ]
        }
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        data = response.json()
        self.assertGreater(data["values"][0]["total_space"], 0)
        self.assertGreater(data["values"][0]["used_space"], 0)
        self.assertGreater(data["values"][0]["free_space"], 0)
        del data["values"][0]["total_space"]
        del data["values"][0]["used_space"]
        del data["values"][0]["free_space"]
        self.assertEqual(expected, data)

    def test_get_3(self):
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
