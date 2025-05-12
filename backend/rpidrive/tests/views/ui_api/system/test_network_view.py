import http

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from rpidrive.views.ui_api.system import SystemNetworkView


class TestSystemNetworkView(TestCase):
    """Test system network view"""

    def setUp(self):
        self.url = "/drive/ui-api/system/network"
        self.admin_user = User.objects.create_superuser("z")
        self.other_user = User.objects.create_user("a")

    def tearDown(self):
        User.objects.all().delete()

    def test_url(self):
        """Test url"""
        self.assertEqual(SystemNetworkView, resolve(self.url).func.view_class)

    def test_get_no_login(self):
        """Test GET method (No login)"""
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FOUND, response.status_code)
        self.assertEqual(b"", response.content)

    def test_get_non_admin(self):
        """Test GET method (No login)"""
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.FORBIDDEN, response.status_code)
        self.assertEqual({"error": ""}, response.json())

    def test_get(self):
        """Test GET method"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(http.HTTPStatus.OK, response.status_code)

        data = response.json()
        self.assertTrue("download_speed" in data)
        self.assertTrue("upload_speed" in data)
        self.assertTrue("downloads" in data)
        self.assertTrue("uploads" in data)

    def test_post(self):
        """Test POST method"""
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_put(self):
        """Test PUT method"""
        self.client.force_login(self.admin_user)
        response = self.client.put(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)

    def test_delete(self):
        """Test DELETE method"""
        self.client.force_login(self.admin_user)
        response = self.client.delete(self.url)
        self.assertEqual(http.HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
