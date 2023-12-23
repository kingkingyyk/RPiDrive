import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.models import Volume, VolumeKindEnum
from rpidrive.views.ui_api.volumes import VolumeCreateView


class TestVolumeCreateView(TestCase):
    """Test VolumeCreateView"""

    def setUp(self):
        self.url = "/drive/ui-api/volumes/create"
        self.admin_user = User.objects.create_superuser("a")
        self.user = User.objects.create_user("z")

    def tearDown(self):
        Volume.objects.all().delete()
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(VolumeCreateView, resolve(self.url).func.view_class)

    def test_get_1(self):
        """Test GET method"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_2(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_post_1(self):
        """Test POST method"""
        post_data = {
            "name": "vol  ",
            "kind": VolumeKindEnum.HOST_PATH,
            "path": "/var",
        }
        self.client.force_login(self.admin_user)

        response = self.client.post(self.url, post_data, "application/json")
        volume = Volume.objects.first()
        self.assertEqual(http.HTTPStatus.CREATED, response.status_code)
        self.assertEqual({"id": str(volume.id)}, response.json())
        self.assertEqual(post_data["name"].strip(), volume.name)
        self.assertEqual(post_data["kind"], volume.kind)
        self.assertEqual(post_data["path"], volume.path)
        self.assertTrue(volume.indexing)

    def test_post_2(self):
        """Test POST method (Normal user)"""
        post_data = {
            "name": "vol",
            "kind": VolumeKindEnum.HOST_PATH,
            "path": "/var",
        }
        self.client.force_login(self.user)

        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": "No permission."}, response.json())
        self.assertEqual(0, Volume.objects.count())

    def test_post_3(self):
        """Test POST method (No login)"""
        post_data = {
            "name": "vol",
            "kind": VolumeKindEnum.HOST_PATH,
            "path": "/var",
        }
        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
        self.assertEqual(0, Volume.objects.count())

    def test_post_4(self):
        """Test POST method (Invalid name)"""
        post_data = {
            "name": "  ",
            "kind": VolumeKindEnum.HOST_PATH,
            "path": "/var",
        }
        self.client.force_login(self.admin_user)

        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Invalid volume name."}, response.json())
        self.assertEqual(0, Volume.objects.count())

    def test_post_5(self):
        """Test POST method (Invalid kind)"""
        post_data = {
            "name": "gg",
            "kind": "ZZZZ",
            "path": "/var",
        }
        self.client.force_login(self.admin_user)

        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {"error": "kind -> Input should be 'hostPath' or 'remoteRpiDrive'"},
            response.json(),
        )
        self.assertEqual(0, Volume.objects.count())

    def test_post_6(self):
        """Test POST method (Invalid path)"""
        post_data = {
            "name": "OK",
            "kind": VolumeKindEnum.HOST_PATH,
            "path": "/rip",
        }
        self.client.force_login(self.admin_user)

        response = self.client.post(self.url, post_data, "application/json")
        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"error": "Path doesn't exist."}, response.json())
        self.assertEqual(0, Volume.objects.count())

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
        """Test DELETE method (No login)"""
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)
