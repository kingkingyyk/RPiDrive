import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.controllers.volume import (
    VolumePermissionModel,
    create_volume,
    update_volume_permission,
)
from rpidrive.models import Volume, VolumeKindEnum, VolumePermissionEnum
from rpidrive.views.ui_api.users import UserListView


class TestUserListView(TestCase):
    """Test UserListView"""

    def setUp(self):
        self.url = "/drive/ui-api/users/"
        self.admin_user = User.objects.create_superuser(
            "a",
            email="a@a.com",
            first_name="b",
            last_name="c",
        )
        self.user = User.objects.create_user(
            "z",
            email="z@x.com",
            first_name="x",
            last_name="y",
        )

    def tearDown(self):
        Volume.objects.all().delete()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(UserListView, resolve(self.url).func.view_class)

    def test_post(self):
        """Test POST method"""
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put(self):
        """Test PUT method"""
        self.client.force_login(self.admin_user)
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete(self):
        """Test DELETE method"""
        self.client.force_login(self.admin_user)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_1(self):
        """Test GET method (Admin)"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        expected = {
            "values": [
                {
                    "id": self.admin_user.id,
                    "username": self.admin_user.username,
                    "first_name": self.admin_user.first_name,
                    "last_name": self.admin_user.last_name,
                    "is_active": self.admin_user.is_active,
                    "is_superuser": self.admin_user.is_superuser,
                },
                {
                    "id": self.user.id,
                    "username": self.user.username,
                    "first_name": self.user.first_name,
                    "last_name": self.user.last_name,
                    "is_active": self.user.is_active,
                    "is_superuser": self.user.is_superuser,
                },
            ]
        }
        actual = response.json()
        self.assertIsNotNone(actual["values"][0]["last_login"])
        del actual["values"][0]["last_login"]
        self.assertIsNone(actual["values"][1]["last_login"])
        del actual["values"][1]["last_login"]
        self.assertEqual(expected, actual)

    def test_get_2(self):
        """Test GET method (Normal user)"""
        volume = create_volume(
            self.admin_user, "HEHE", VolumeKindEnum.HOST_PATH, "/var/"
        )
        update_volume_permission(
            self.admin_user,
            str(volume.id),
            [
                VolumePermissionModel(
                    user=self.user.pk,
                    permission=VolumePermissionEnum.READ_WRITE,
                )
            ],
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        expected = {
            "values": [
                {
                    "id": self.admin_user.id,
                    "username": self.admin_user.username,
                    "first_name": self.admin_user.first_name,
                    "last_name": self.admin_user.last_name,
                },
                {
                    "id": self.user.id,
                    "username": self.user.username,
                    "first_name": self.user.first_name,
                    "last_name": self.user.last_name,
                },
            ]
        }
        self.assertEqual(expected, response.json())

    def test_get_3(self):
        """Test GET method (Normal user)"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
