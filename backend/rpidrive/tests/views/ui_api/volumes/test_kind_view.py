import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.views.ui_api.volumes import VolumeKindView


class TestVolumeKindView(TestCase):
    """Test VolumeKindView"""

    def setUp(self):
        self.url = "/drive/ui-api/volumes/kinds"
        self.admin_user = User.objects.create_superuser("a")
        self.user = User.objects.create_user("z")

    def tearDown(self):
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(VolumeKindView, resolve(self.url).func.view_class)

    def test_post_1(self):
        """Test POST method"""
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_2(self):
        """Test POST method (No login)"""
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_1(self):
        """Test GET method"""
        expected = {
            "values": [
                {"name": "Local Storage", "value": "hostPath"},
                {
                    "name": "Remote RPI Drive",
                    "value": "remoteRpiDrive",
                },
            ]
        }

        users = [self.admin_user, self.user]
        for user in users:
            self.client.force_login(user)
            response = self.client.get(self.url)
            self.assertEqual(http.HTTPStatus.OK, response.status_code)
            self.assertEqual(expected, response.json())
            self.client.logout()

    def test_get_2(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_put_1(self):
        """Test PUT method"""
        self.client.force_login(self.admin_user)
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
        self.client.force_login(self.admin_user)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_delete_2(self):
        """Test DELETE method"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
